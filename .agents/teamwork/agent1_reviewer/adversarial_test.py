import asyncio
import os
import sys
import tempfile
import time

# Add root of core-engine to sys.path
sys.path.insert(0, r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine")

from src.services.conversation_store import ConversationStore

async def stress_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "adversarial.db")
        store = ConversationStore(db_path)
        await store.init_db()

        # 1. Concurrency Stress Test: 50 concurrent writes across async tasks
        conv_id = "stress_conv_01"
        await store.create_conversation(id=conv_id, title="Concurrency Test")

        async def write_turn(idx):
            await store.add_message(
                conversation_id=conv_id,
                role="user" if idx % 2 == 0 else "assistant",
                content=f"Message {idx} with emoji 🚀 and unicode: 你好 monde",
                cards=[{"type": "test", "data": {"idx": idx}}] if idx % 5 == 0 else None
            )

        await asyncio.gather(*(write_turn(i) for i in range(50)))

        conv = await store.get_conversation(conv_id, include_messages=True)
        assert conv["turns_count"] == 50, f"Expected 50 turns, got {conv['turns_count']}"
        print("[PASS] Concurrency: 50 simultaneous writes handled without lock error or data loss")

        # 2. SQL Injection & Hostile Payloads
        malicious_inputs = [
            "' OR '1'='1\"; DROP TABLE conversations; --",
            "<script>alert('xss')</script>",
            "\x00nullbyte",
            "Emoji 🔥🎉🚀👽👻 test",
            "A" * 10000  # 10KB string
        ]
        for idx, payload in enumerate(malicious_inputs):
            m_id = f"inj_{idx}"
            await store.create_conversation(id=m_id, title=payload, metadata={"inj": payload})
            await store.add_message(m_id, "user", payload)
            fetched = await store.get_conversation(m_id, include_messages=True)
            assert fetched is not None, f"Failed on payload {idx}"
            assert fetched["title"] == payload
            assert fetched["messages"][0]["content"] == payload
        print("[PASS] SQL Injection & hostile payloads: perfectly sanitized and safely persisted")

        # 3. NLP Titling Edge Cases
        edge_texts = [
            ("", "Nouvelle discussion"),
            ("   ", "Nouvelle discussion"),
            ("?!?!??", "Nouvelle discussion"),
            ("bonjour salut stp merci", "Bonjour salut stp merci"),
            ("Un deux trois quatre cinq six sept huit neuf dix", "Deux trois quatre cinq six"),
            ("A" * 200, 38)
        ]
        for raw, expected in edge_texts:
            t = store.generate_nlp_title(raw)
            if isinstance(expected, int):
                assert len(t) <= expected, f"Title length {len(t)} exceeded {expected}"
            else:
                assert t == expected, f"For '{raw}', expected '{expected}', got '{t}'"
        print("[PASS] Auto-titling edge cases: correctly fall back or truncate without exception")

        # 4. Exports with empty data
        empty_id = "empty_conv"
        await store.create_conversation(id=empty_id, title="Vide")
        md = await store.export_conversation_markdown(empty_id)
        assert "# Vide" in md
        js = await store.export_conversation_json(empty_id)
        assert js["conversation"]["turns_count"] == 0
        print("[PASS] Markdown & JSON exports: handle empty and minimal conversations cleanly")

        # 5. Boundary Condition: Non-existent conversation handling
        non_existent = await store.get_conversation("does_not_exist")
        assert non_existent is None
        del_res = await store.delete_conversation("does_not_exist")
        assert del_res is False
        print("[PASS] Missing entity handling: returns None and False cleanly without crashing")

if __name__ == "__main__":
    asyncio.run(stress_test())
