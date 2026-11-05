"""
Planificateur d'intentions (Planner DAG) pour l'Agent Manager de HoL AI.
Décompose une intention complexe en un graphe acyclique dirigé (DAG) de sous-tâches typées.
"""
import re
from typing import List, Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from src.core.contracts import AgentID, ActionType, PriorityEnum, ContextModel


class CyclicDependencyError(ValueError):
    """Exception levée lorsqu'un cycle de dépendances est détecté dans le DAG."""
    pass


class DependencyError(ValueError):
    """Exception levée lorsqu'une dépendance de tâche est invalide ou corrompue."""
    pass


class SubTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    target_agent: AgentID
    action: ActionType
    payload: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[Optional[str]] = Field(default_factory=list)
    priority: PriorityEnum = PriorityEnum.MEDIUM
    timeout_seconds: Optional[float] = None


class ExecutionPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid4().hex[:8]}")
    original_intent: str
    context: ContextModel
    tasks: List[SubTask]
    estimated_total_steps: int = 0


class IntentPlanner:
    """
    Analyse les requêtes complexes et formule un plan d'action multi-agents.
    """

    @classmethod
    def create_plan_from_intent(cls, intent_text: str, context: Optional[ContextModel] = None) -> ExecutionPlan:
        if context is None:
            context = ContextModel(user_id="default_user", session_id="default_sess")
        intent_lower = intent_text.lower()
        tasks: List[SubTask] = []

        # Détection d'intention composite 1 : Logistique + Finance + Canvas
        # Ex: "Suis mon colis 1Z123, calcule ma marge sur le produit à 120€ (coût 50€) et ajoute un bloc sur le canevas"
        has_logistics = any(k in intent_lower for k in ["colis", "suivi", "track", "livraison", "transporteur", "ups", "dhl"])
        has_finance = any(k in intent_lower for k in ["marge", "rentabilité", "finance", "bénéfice", "coût", "prix de vente"])
        has_canvas = any(k in intent_lower for k in ["canevas", "canvas", "workspace", "bloc", "note", "carte", "affiche"])
        has_content = any(k in intent_lower for k in ["script", "tiktok", "reels", "contenu", "viral", "post", "telegram"])
        has_execution = any(k in intent_lower for k in ["bloqué", "procrastin", "tâche", "micro-action", "planifie", "objectif"])

        task_logistics_id: Optional[str] = None
        task_finance_id: Optional[str] = None

        if has_logistics:
            t_log = SubTask(
                target_agent=AgentID.AGENT_3_LOGISTICS,
                action=ActionType.TRACK_SHIPMENT,
                payload={
                    "tracking_number": "1Z9999999999FR",
                    "carrier": "UPS",
                    "notify_on_change": True
                },
                priority=PriorityEnum.HIGH
            )
            task_logistics_id = t_log.task_id
            tasks.append(t_log)

        if has_finance:
            depends = [task_logistics_id] if task_logistics_id else []
            t_fin = SubTask(
                target_agent=AgentID.AGENT_4_FINANCE,
                action=ActionType.AUDIT_MARGINS,
                payload={
                    "selling_price": 120.0,
                    "cost_price": 45.0,
                    "platform_fee_percent": 0.15,
                    "vat_percent": 0.20
                },
                depends_on=depends,
                priority=PriorityEnum.HIGH
            )
            task_finance_id = t_fin.task_id
            tasks.append(t_fin)

        if has_canvas:
            depends = []
            if task_finance_id:
                depends.append(task_finance_id)
            elif task_logistics_id:
                depends.append(task_logistics_id)

            t_can = SubTask(
                target_agent=AgentID.AGENT_1_CANVAS,
                action=ActionType.CREATE_CANVAS_NODE,
                payload={
                    "type": "summary_card",
                    "title": "Synthèse Opérationnelle HoL AI",
                    "position": {"x": 200, "y": 150},
                    "auto_link": True
                },
                depends_on=depends,
                priority=PriorityEnum.MEDIUM
            )
            tasks.append(t_can)

        # 1. Détection Prioritaire E-Commerce, Shopping & Chasseur de Prix Universel (Tech, Beauté, Occasion, etc.)
        is_tech_or_shopping = any(k in intent_lower for k in [
            "cdiscount", "amazon", "fnac", "ldlc", "aliexpress", "darty", "boulanger", "leboncoin", "alibaba",
            "vinted", "backmarket", "back market", "sephora", "nocibe", "nocibé", "rakuten", "ebay",
            "pc", "ordinateur", "portable", "laptop", "gpu", "carte graphique", "5060", "4060", "3060", "rtx",
            "ps5", "playstation", "console", "iphone", "smartphone", "tablette", "écran", "casque",
            "maquillage", "palette", "crème", "creme", "soin", "fard", "fards", "beauté", "parfum", "sérum",
            "sneakers", "baskets", "vêtement", "vetement", "sac", "aspirateur",
            "trouve", "trouve moi", "cherche", "cherche moi", "le moins cher", "le moin cher", "le moin chère",
            "la moins chère", "pas cher", "prix bas", "meilleur prix", "deal", "promo", "baisse de prix",
            "acheter", "achat", "fournisseur", "occasion", "reconditionné", "reconditionne", "seconde main"
        ])

        detected_platform = "Web"
        if "cdiscount" in intent_lower:
            detected_platform = "Cdiscount"
        elif "amazon" in intent_lower:
            detected_platform = "Amazon"
        elif "fnac" in intent_lower:
            detected_platform = "Fnac"
        elif "ldlc" in intent_lower:
            detected_platform = "LDLC"
        elif "leboncoin" in intent_lower:
            detected_platform = "Leboncoin"
        elif "vinted" in intent_lower:
            detected_platform = "Vinted"
        elif "backmarket" in intent_lower or "back market" in intent_lower:
            detected_platform = "Back Market"
        elif "sephora" in intent_lower:
            detected_platform = "Sephora"
        elif "nocibe" in intent_lower or "nocibé" in intent_lower:
            detected_platform = "Nocibé"
        elif "rakuten" in intent_lower:
            detected_platform = "Rakuten"
        elif "ebay" in intent_lower:
            detected_platform = "eBay"

        # 2. Détection d'intentions Muse AI Piliers 1 à 6
        has_recipe = any(k in intent_lower for k in ["recette", "courses", "ingrédient", "tiktok recette"]) or ("instagram" in intent_lower and any(w in intent_lower for w in ["pâtes", "saumon", "plat", "recette", "cuisine"]))
        
        # Réservation : Strictement réservé aux restaurants et voyages (NE JAMAIS MATCHER SUR "PORTABLE" !)
        has_reservation = (not is_tech_or_shopping) and any(
            re.search(rf"\b{re.escape(k)}\b", intent_lower) 
            for k in ["réserve", "réserver", "réservation", "restaurant", "resto", "table pour", "voyage", "billet d'avion", "billets d'avion", "vol pour"]
        )
        has_inbox = any(k in intent_lower for k in ["email", "mails", "inbox", "boîte de réception", "trie mes mails"])
        has_vault = any(k in intent_lower for k in ["vm", "enclave", "vault", "sécurité", "coffre"])

        if has_recipe:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.RECIPE_TO_GROCERY,
                    payload={"recipe": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_reservation:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.BOOK_RESERVATION,
                    payload={"details": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_inbox:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.CLEAN_INBOX,
                    payload={"scope": "unread"},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_vault:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.SECURE_VM_AUDIT,
                    payload={},
                    priority=PriorityEnum.MEDIUM
                )
            )

        has_calendar = any(k in intent_lower for k in ["calendrier", "agenda", "réunion", "meeting", "rendez-vous", "conflit d'agenda", "planning"])
        if has_calendar:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.MANAGE_CALENDAR,
                    payload={"details": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        has_sandbox_code = any(k in intent_lower for k in ["exécute le code", "execute code", "sandbox", "exécute ce code", "script dans la vm"])
        if has_sandbox_code:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.EXECUTE_SANDBOX_CODE,
                    payload={"code": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        has_subscriptions = any(k in intent_lower for k in ["abonnement", "subscription", "frais caché", "récurrent", "saas", "charges"])
        has_meta_ads = any(k in intent_lower for k in ["meta ad", "ads", "pub", "instagram", "roas", "campagne facebook", "cpa"])
        has_autonomous = any(k in intent_lower for k in ["autonome", "24/7", "surveillance", "gardien", "arrière-plan", "background", "veille", "surveille"])
        has_sourcing = any(k in intent_lower for k in ["sourcing", "compare les fournisseurs", "comparateur de fournisseurs", "fournisseurs direct", "grossiste"]) and not ("surveille" in intent_lower or "5060" in intent_lower or "ps5" in intent_lower)
        has_reconciliation = any(k in intent_lower for k in ["rapprochement", "affiliation", "commissions d'affiliation", "opex"])
        has_invoice = any(k in intent_lower for k in ["facture", "reçu", "justificatif", "ticket de caisse", "note de frais"])

        if has_sourcing:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_3_LOGISTICS,
                    action=ActionType.FIND_SUPPLIERS,
                    payload={"product": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_reconciliation:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_4_FINANCE,
                    action=ActionType.RECONCILE_TRANSACTIONS,
                    payload={},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_invoice:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_4_FINANCE,
                    action=ActionType.EXTRACT_INVOICE_DATA,
                    payload={"raw_text": intent_text},
                    priority=PriorityEnum.HIGH
                )
            )

        if is_tech_or_shopping:
            target_price = 450.0
            if any(k in intent_lower for k in ["5060", "4060", "portable", "pc", "laptop"]):
                target_price = 800.0
            
            payload_data = {
                "product": intent_text,
                "platform": detected_platform,
                "target_price": target_price
            }
            if context:
                res_prod = getattr(context, "extra_metadata", {}).get("resolved_product") or getattr(context, "metadata", {}).get("resolved_product")
                if res_prod:
                    payload_data["context_product"] = res_prod

            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_3_LOGISTICS,
                    action=ActionType.WATCH_PRICE_DROP,
                    payload=payload_data,
                    priority=PriorityEnum.HIGH
                )
            )

        if has_subscriptions:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_4_FINANCE,
                    action=ActionType.AUDIT_SUBSCRIPTIONS,
                    payload={"audit_scope": "all_connected_services"},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_meta_ads:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_5_CONTENT,
                    action=ActionType.AUDIT_META_ADS,
                    payload={"timeframe": "last_7_days"},
                    priority=PriorityEnum.HIGH
                )
            )

        if has_autonomous:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_6_EXECUTION,
                    action=ActionType.START_AUTONOMOUS_WATCHER,
                    payload={"mode": "full_business_guardian"},
                    priority=PriorityEnum.CRITICAL
                )
            )

        if has_execution:
            t_exec = SubTask(
                target_agent=AgentID.AGENT_6_EXECUTION,
                action=ActionType.BREAKDOWN_GOAL,
                payload={"goal": intent_text},
                priority=PriorityEnum.CRITICAL
            )
            tasks.append(t_exec)

        # Si aucune intention spécifique n'est matchée, tâche par défaut sur le canevas
        if not tasks:
            tasks.append(
                SubTask(
                    target_agent=AgentID.AGENT_1_CANVAS,
                    action=ActionType.CREATE_CANVAS_NODE,
                    payload={"content": intent_text, "type": "note_card"},
                    priority=PriorityEnum.LOW
                )
            )

        plan = ExecutionPlan(
            original_intent=intent_text,
            context=context,
            tasks=tasks,
            estimated_total_steps=len(tasks)
        )
        cls.validate_plan(plan)
        return plan

    @classmethod
    def validate_plan(cls, plan: ExecutionPlan) -> None:
        """
        Valide la cohérence du DAG d'exécution :
        Détecte les dépendances cycliques (A -> B -> A, auto-dépendance A -> A, etc.).
        Lève CyclicDependencyError si un cycle existe.
        """
        task_ids = {t.task_id for t in plan.tasks}
        graph: Dict[str, List[str]] = {t.task_id: [] for t in plan.tasks}

        for task in plan.tasks:
            for dep in task.depends_on:
                if dep and dep in task_ids:
                    graph[task.task_id].append(dep)

        # Détection de cycle via DFS (0=UNVISITED, 1=VISITING, 2=VISITED)
        visited: Dict[str, int] = {t.task_id: 0 for t in plan.tasks}

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            for neighbor in graph.get(node, []):
                if visited.get(neighbor) == 1:
                    cycle = " -> ".join(path + [neighbor])
                    raise CyclicDependencyError(f"Cycle détecté dans le DAG : {cycle}")
                if visited.get(neighbor) == 0:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2

        for t_id in task_ids:
            if visited[t_id] == 0:
                dfs(t_id, [t_id])

    @classmethod
    def topological_sort_tasks(cls, tasks: List[SubTask]) -> List[SubTask]:
        """
        Trie les tâches selon l'ordre topologique de leurs dépendances.
        Les tâches sans dépendances sont ordonnancées en premier.
        """
        task_map = {t.task_id: t for t in tasks}
        in_degree = {t.task_id: 0 for t in tasks}
        dependents: Dict[str, List[str]] = {t.task_id: [] for t in tasks}

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id and dep_id in task_map:
                    in_degree[task.task_id] += 1
                    dependents[dep_id].append(task.task_id)

        queue = [t for t in tasks if in_degree[t.task_id] == 0]
        sorted_tasks = []

        while queue:
            current = queue.pop(0)
            sorted_tasks.append(current)
            for dep_task_id in dependents.get(current.task_id, []):
                in_degree[dep_task_id] -= 1
                if in_degree[dep_task_id] == 0:
                    queue.append(task_map[dep_task_id])

        # S'il reste des tâches non résolues (ex: dépendance orpheline), les ajouter à la fin
        for t in tasks:
            if t not in sorted_tasks:
                sorted_tasks.append(t)

        return sorted_tasks
