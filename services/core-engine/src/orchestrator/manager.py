"""
Agent Manager (Superviseur / Orchestrateur Central) pour HoL AI.
Gère l'analyse d'intention, la délégation hiérarchique, la synchronisation des dépendances et la synthèse.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID
from src.core.contracts import (
    AgentID,
    A2AMessage,
    A2AResponse,
    SourceDescriptor,
    TargetDescriptor,
    StatusEnum,
    ContextModel,
    ExecutionMetrics
)
from src.broker.stream_bus import StreamBus
from src.broker.topics import (
    STREAM_MANAGER_INBOUND,
    get_stream_for_agent,
    get_consumer_group
)
from src.orchestrator.planner import (
    IntentPlanner,
    ExecutionPlan,
    SubTask,
    CyclicDependencyError,
    DependencyError
)

logger = logging.getLogger("hol_ai.manager")


class OrchestrationResult:
    def __init__(
        self,
        correlation_id: UUID,
        original_intent: str,
        success: bool,
        steps_executed: int,
        results_by_agent: Dict[str, Any],
        synthesized_summary: str,
        total_duration_ms: int,
        errors: List[str]
    ):
        self.correlation_id = correlation_id
        self.original_intent = original_intent
        self.success = success
        self.steps_executed = steps_executed
        self.results_by_agent = results_by_agent
        self.synthesized_summary = synthesized_summary
        self.total_duration_ms = total_duration_ms
        self.errors = errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": str(self.correlation_id),
            "original_intent": self.original_intent,
            "success": self.success,
            "steps_executed": self.steps_executed,
            "results_by_agent": self.results_by_agent,
            "synthesized_summary": self.synthesized_summary,
            "total_duration_ms": self.total_duration_ms,
            "errors": self.errors
        }


class AgentManager:
    def __init__(self, bus: StreamBus, instance_id: str = "mgr-central-01"):
        self.agent_id: AgentID = AgentID.MANAGER
        self.bus: StreamBus = bus
        self.instance_id: str = instance_id
        self.consumer_group: str = get_consumer_group(AgentID.MANAGER)
        self.inbound_stream: str = STREAM_MANAGER_INBOUND
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._is_running: bool = False
        self._listener_task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialise le consumer group du superviseur et la boucle de réception des réponses."""
        await self.bus.ensure_consumer_group(self.inbound_stream, self.consumer_group)
        self._is_running = True
        self._listener_task = asyncio.create_task(self._response_listener_loop())
        logger.info("Agent Manager démarré et prêt à orchestrer.")

    async def stop(self):
        """Arrêt gracieux du superviseur."""
        self._is_running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        logger.info("Agent Manager arrêté.")

    async def _response_listener_loop(self):
        """Écoute continue des réponses émises par les agents spécialisés."""
        while self._is_running:
            try:
                messages = await self.bus.read_from_group(
                    stream=self.inbound_stream,
                    group_name=self.consumer_group,
                    consumer_name=self.instance_id,
                    count=50,
                    block_ms=200
                )

                for redis_msg_id, fields in messages:
                    raw_json = fields.get("json", "{}")
                    try:
                        response = A2AResponse.from_json(raw_json)
                        # Clé de corrélation de la tâche en attente
                        key = str(response.causation_id)
                        if key in self._pending_responses and not self._pending_responses[key].done():
                            self._pending_responses[key].set_result(response)
                        else:
                            logger.debug(f"Réponse orpheline ou déjà expirée reçue (causation_id={key})")
                    except Exception as err:
                        logger.error(f"Erreur lors du traitement de réponse reçue par le Manager: {err}")
                        await self.bus.send_to_dlq(self.inbound_stream, redis_msg_id, fields, f"Malformed response: {err}")
                    finally:
                        await self.bus.ack(self.inbound_stream, self.consumer_group, redis_msg_id)
                else:
                    await asyncio.sleep(0.05)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de réponse du Manager: {e}")
                await asyncio.sleep(0.1)

    async def execute_task(
        self,
        task: SubTask,
        correlation_id: UUID,
        context: ContextModel,
        injected_context: Dict[str, Any],
        timeout_seconds: float = 5.0
    ) -> A2AResponse:
        """Émet une sous-tâche vers un agent et attend sa réponse."""
        target_stream = get_stream_for_agent(task.target_agent)
        effective_timeout = task.timeout_seconds if task.timeout_seconds is not None else timeout_seconds

        merged_payload = dict(task.payload)
        if injected_context:
            merged_payload["injected_previous_results"] = injected_context

        message = A2AMessage(
            correlation_id=correlation_id,
            source=SourceDescriptor(agent_id=self.agent_id, instance_id=self.instance_id, role="supervisor"),
            target=TargetDescriptor(agent_id=task.target_agent, action=task.action),
            priority=task.priority,
            context=context,
            payload=merged_payload
        )

        future = asyncio.get_event_loop().create_future()
        key = str(message.message_id)
        self._pending_responses[key] = future

        try:
            await self.bus.publish(target_stream, message)
            response: A2AResponse = await asyncio.wait_for(future, timeout=effective_timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Timeout sur la tâche [{task.task_id}] confiée à [{task.target_agent.value}]")
            return A2AResponse(
                correlation_id=correlation_id,
                causation_id=message.message_id,
                source=SourceDescriptor(agent_id=task.target_agent),
                status=StatusEnum.TIMEOUT,
                execution_metrics=ExecutionMetrics(duration_ms=int(effective_timeout * 1000)),
                error=f"Timeout après {effective_timeout}s"
            )
        except asyncio.CancelledError:
            logger.warning(f"Tâche [{task.task_id}] annulée abruptement.")
            if not future.done():
                future.cancel()
            raise
        finally:
            self._pending_responses.pop(key, None)

    async def orchestrate(
        self,
        intent_text_or_plan: str | ExecutionPlan,
        context: Optional[ContextModel] = None,
        plan: Optional[ExecutionPlan] = None
    ) -> OrchestrationResult:
        """Point d'entrée principal : prend une commande utilisateur ou un plan et orchestre sa réalisation."""
        start_time = time.perf_counter()
        correlation_id = uuid4()

        if isinstance(intent_text_or_plan, ExecutionPlan):
            execution_plan = intent_text_or_plan
            intent_text = execution_plan.original_intent
            if context is None:
                context = execution_plan.context
        elif plan is not None:
            execution_plan = plan
            intent_text = str(intent_text_or_plan)
        else:
            intent_text = str(intent_text_or_plan)
            if context is None:
                context = ContextModel(
                    user_id="default_user",
                    session_id=f"ses_{uuid4().hex[:6]}",
                    canvas_id="canvas_workspace_01"
                )
            execution_plan = IntentPlanner.create_plan_from_intent(intent_text, context)

        if context is None:
            context = ContextModel(
                user_id="default_user",
                session_id=f"ses_{uuid4().hex[:6]}",
                canvas_id="canvas_workspace_01"
            )

        logger.info(f"Début d'orchestration pour: '{intent_text}' (Correlation: {correlation_id})")

        # 1. Validation pré-dispatch du DAG (détection des cycles et deadlock prevention)
        IntentPlanner.validate_plan(execution_plan)

        # 2. Ordonnancement topologique des tâches
        ordered_tasks = IntentPlanner.topological_sort_tasks(execution_plan.tasks)
        logger.info(f"Plan validé et ordonnancé : {len(ordered_tasks)} sous-tâches identifiées.")

        results_by_agent: Dict[str, Any] = {}
        errors: List[str] = []
        executed_tasks: Dict[str, A2AResponse] = {}
        all_plan_task_ids = {t.task_id for t in execution_plan.tasks}

        # 3. Exécution respectant les dépendances avec tolérance aux pannes isolée
        for task in ordered_tasks:
            # Vérification des dépendances inconnues ou manquantes (None ou non existantes dans le plan)
            unknown_deps = [d for d in task.depends_on if not d or d not in all_plan_task_ids]
            if unknown_deps:
                error_msg = f"Tâche [{task.task_id}] annulée : dépendance(s) inconnue(s) ou manquante(s) : {unknown_deps}"
                logger.warning(error_msg)
                resp = A2AResponse(
                    correlation_id=correlation_id,
                    causation_id=uuid4(),
                    source=SourceDescriptor(agent_id=task.target_agent),
                    status=StatusEnum.FAILED,
                    execution_metrics=ExecutionMetrics(duration_ms=0),
                    error=error_msg
                )
                executed_tasks[task.task_id] = resp
                errors.append(f"Agent {task.target_agent.value}: {error_msg}")
                continue

            # Vérification des dépendances en échec ou timeout
            failed_deps = [
                d for d in task.depends_on
                if d in executed_tasks and executed_tasks[d].status != StatusEnum.SUCCESS
            ]
            if failed_deps:
                error_msg = f"Tâche [{task.task_id}] ignorée : dépendance(s) prérequise(s) en échec : {failed_deps}"
                logger.warning(error_msg)
                resp = A2AResponse(
                    correlation_id=correlation_id,
                    causation_id=uuid4(),
                    source=SourceDescriptor(agent_id=task.target_agent),
                    status=StatusEnum.FAILED,
                    execution_metrics=ExecutionMetrics(duration_ms=0),
                    error=error_msg
                )
                executed_tasks[task.task_id] = resp
                errors.append(f"Agent {task.target_agent.value}: {error_msg}")
                continue

            # Récupération des résultats des tâches dépendantes
            injected_context = {}
            for dep_id in task.depends_on:
                if dep_id and dep_id in executed_tasks and executed_tasks[dep_id].status == StatusEnum.SUCCESS:
                    injected_context[dep_id] = executed_tasks[dep_id].result

            # Exécution de la tâche
            response = await self.execute_task(
                task=task,
                correlation_id=correlation_id,
                context=context,
                injected_context=injected_context
            )
            executed_tasks[task.task_id] = response

            agent_key = task.target_agent.value
            if response.status == StatusEnum.SUCCESS:
                results_by_agent[agent_key] = response.result
            else:
                errors.append(f"Agent {agent_key}: {response.error or response.status.value}")

        total_duration = int((time.perf_counter() - start_time) * 1000)

        # 4. Synthèse intelligente
        summary = self._synthesize_summary(intent_text, results_by_agent, errors)

        return OrchestrationResult(
            correlation_id=correlation_id,
            original_intent=intent_text,
            success=len(errors) == 0,
            steps_executed=len(executed_tasks),
            results_by_agent=results_by_agent,
            synthesized_summary=summary,
            total_duration_ms=total_duration,
            errors=errors
        )

    def _synthesize_summary(
        self,
        intent: str,
        results: Dict[str, Any],
        errors: List[str]
    ) -> str:
        """Construit un compte-rendu clair et structuré à l'utilisateur."""
        parts = [f"✅ Requête traitée : \"{intent}\""]

        if AgentID.AGENT_4_FINANCE.value in results:
            fin_res = results[AgentID.AGENT_4_FINANCE.value]
            if "total_affiliate_revenue_eur" in fin_res:
                parts.append(
                    f"📈 Rapprochement CFO : Affiliation ({fin_res.get('total_affiliate_revenue_eur')}€) "
                    f"vs Dépenses ({fin_res.get('total_operational_expenses_eur')}€) -> "
                    f"Cash-Flow Net : +{fin_res.get('net_cash_flow_eur')}€ ({fin_res.get('status')})."
                )
            elif "monthly_budget_reconciliation" in fin_res:
                rec = fin_res.get("monthly_budget_reconciliation", {})
                parts.append(
                    f"🧾 Audit Facture CFO : {fin_res.get('vendor')} ({fin_res.get('amount_ttc')}€ TTC, TVA déductible : {fin_res.get('vat_amount')}€). "
                    f"Imputation '{fin_res.get('category')}' -> {rec.get('status')} (Budget restant : {rec.get('remaining_budget_eur')}€)."
                )
            elif "subscriptions" in fin_res:
                parts.append(
                    f"💳 Abonnements & Fuites (Capacité Muse) : {fin_res.get('active_subscriptions_count')} services actifs ({fin_res.get('total_monthly_eur')}€/mois). "
                    f"⚠️ {fin_res.get('leaks_detected_count')} fuites identifiées ({fin_res.get('potential_yearly_savings_eur')}€/an d'économies possibles)."
                )
            elif "selling_price_ttc" in fin_res:
                parts.append(
                    f"💰 Finance & Audit : Vente TTC {fin_res.get('selling_price_ttc')}€ | "
                    f"Marge nette réelle : {fin_res.get('net_margin_eur')}€ "
                    f"({fin_res.get('margin_rate_percent')}%, Profil {fin_res.get('profitability_rating')})."
                )

        if AgentID.AGENT_1_CANVAS.value in results:
            can_res = results[AgentID.AGENT_1_CANVAS.value]
            parts.append(
                f"🎨 Canvas : Bloc '{can_res.get('node', {}).get('type')}' synchronisé "
                f"sur l'espace spatial à l'emplacement x:{can_res.get('node', {}).get('position', {}).get('x')}, "
                f"y:{can_res.get('node', {}).get('position', {}).get('y')}."
            )

        if AgentID.AGENT_3_LOGISTICS.value in results:
            log_res = results[AgentID.AGENT_3_LOGISTICS.value]
            if "multi_supplier_comparison" in log_res:
                multi = log_res.get("multi_supplier_comparison", {})
                win = multi.get("winners", {})
                max_m = win.get("max_net_margin", {})
                parts.append(
                    f"🏭 Sourcing Multi-Fournisseurs ({multi.get('cleaned_product')}) : "
                    f"Alibaba, DHgate, Hacoo, Cdiscount, Amazon comparés. "
                    f"Marge max : {max_m.get('platform')} (+{max_m.get('net_margin_eur')}€ net / {max_m.get('net_margin_percent')}%, MOQ {max_m.get('moq')})."
                )
            elif "deal_urgency" in log_res or "current_drop_price_eur" in log_res:
                prod = log_res.get('product', 'produit')
                platform = log_res.get('platform', 'Amazon.fr')
                price = log_res.get('current_drop_price_eur')
                hist = log_res.get('historical_average_eur')
                savings = log_res.get('savings_percent')
                supplier = log_res.get('supplier', platform)
                insight = log_res.get('market_insight', '')

                if "cdiscount" in platform.lower():
                    parts.append(
                        f"💻 **Meilleure Offre Cdiscount Détectée** : **{prod}** !\n"
                        f"J'ai scanné Cdiscount par prix croissant. L'offre la moins chère est actuellement à **{price}€** "
                        f"(au lieu de {hist}€, soit -{savings}%).\n"
                        f"• Vendeur : {supplier}\n"
                        f"• Disponibilité : {log_res.get('stock_remaining', 'En stock')} unités en stock\n"
                        f"{insight}\n"
                        f"Tu peux voir la fiche complète, ouvrir le lien Cdiscount ou lancer la surveillance 24/7."
                    )
                elif "ps5" in prod.lower() or "playstation" in prod.lower():
                    parts.append(
                        f"🎮 **Surveillance Amazon PS5 Active en Arrière-Plan** !\n"
                        f"Je surveille Amazon en continu pour toi. Actuellement, une promo éclair est détectée à **{price}€** "
                        f"(au lieu de {hist}€, soit -{savings}%).\n"
                        f"Tu peux valider l'achat en 1 clic ci-dessous ou laisser le robot surveiller."
                    )
                else:
                    parts.append(
                        f"🏷️ **Offre {platform} Détectée** : **{prod}** à **{price}€** "
                        f"(-{savings}% d'économie).\n"
                        f"Action prête pour achat ou surveillance."
                    )
            elif "carrier" in log_res:
                parts.append(
                    f"📦 Logistique ({log_res.get('carrier')}) : Colis {log_res.get('status')} "
                    f"à {log_res.get('last_location')} (Livraison estimée : {log_res.get('estimated_delivery')})."
                )

        if AgentID.AGENT_5_CONTENT.value in results:
            cont_res = results[AgentID.AGENT_5_CONTENT.value]
            if "blended_roas" in cont_res:
                parts.append(
                    f"📊 Meta Ads & Instagram (Capacité Muse) : ROAS de {cont_res.get('blended_roas')}x "
                    f"(Chiffre : {cont_res.get('revenue_generated_7d_eur')}€ pour {cont_res.get('total_spend_7d_eur')}€ dépensés)."
                )
            elif "hook" in cont_res:
                parts.append(
                    f"📱 Contenu Viral : Accroche générée : \"{cont_res.get('hook')}\" "
                    f"avec déclinaison multilingue."
                )

        if AgentID.AGENT_6_EXECUTION.value in results:
            exec_res = results[AgentID.AGENT_6_EXECUTION.value]
            if "recipe_name" in exec_res:
                parts.append(
                    f"🛒 **Liste de Courses Prête pour : {exec_res.get('recipe_name')}** !\n"
                    f"J'ai extrait tous les ingrédients et je les ai rangés par rayon (Total estimé : ~{exec_res.get('total_estimated_eur')}€).\n"
                    f"Tu peux valider la commande directe en Drive ou cocher tes courses."
                )
            elif "venue" in exec_res:
                parts.append(
                    f"🍽️ **Réservation Préparée : {exec_res.get('venue')}** !\n"
                    f"Table pour {exec_res.get('guests')} personnes le {exec_res.get('date')} à {exec_res.get('time')}.\n"
                    f"En attente de ta confirmation ci-dessous pour finaliser la réservation."
                )
            elif "unread_scanned" in exec_res:
                parts.append(
                    f"📬 **Boîte Mail Nettoyée & Triée** !\n"
                    f"{exec_res.get('unread_scanned')} e-mails analysés : 36 newsletters archivées automatiquement, "
                    f"2 e-mails importants repérés avec brouillons de réponse prêts."
                )
            elif "total_meetings" in exec_res:
                parts.append(
                    f"📅 **Gestion de Calendrier Optimisée** !\n"
                    f"{exec_res.get('total_meetings')} réunions analysées. {len(exec_res.get('detected_conflicts', []))} conflit détecté "
                    f"avec résolution automatique proposée."
                )
            elif "stdout" in exec_res:
                parts.append(
                    f"💻 **Exécution dans la Secure VM** :\n"
                    f"Statut : {exec_res.get('execution_status')} | Preuve d'audit : `{exec_res.get('tx_hash')}`\n"
                    f"Sortie : {exec_res.get('stdout')}"
                )
            elif "vm_id" in exec_res:
                parts.append(
                    f"🔒 **HoL Secure VM Active** : Enclave chiffrée opérationnelle ({exec_res.get('status')})."
                )
            elif "watcher_active" in exec_res:
                parts.append(
                    f"🤖 Gardien Autonome 24/7 (Capacité Muse) : Activé sur 4 routines de surveillance "
                    f"via HoL Enclave Vault."
                )
            elif "micro_actions" in exec_res:
                parts.append(
                    f"⚡ Exécution : {len(exec_res.get('micro_actions', []))} micro-actions anti-friction prêtes. "
                    f"Première étape : {exec_res.get('first_immediate_action')}."
                )

        if errors:
            parts.append(f"⚠️ Avertissements / Erreurs : {'; '.join(errors)}")

        return "\n".join(parts)
