from langchain_core.messages import AIMessage
import pytest

def test_tutor_reply_extracts_text_from_gemini_content_blocks(monkeypatch):
    # conftest has configured an isolated database before this import.
    from app import ai_service

    class FakeLLM:
        def invoke(self, prompt):
            return AIMessage(content=[
                {"type": "text", "text": "Hãy kiểm tra dữ liệu.", "extras": {"signature": "internal"}},
            ])

    monkeypatch.setattr(ai_service, "_load_graph", lambda: (None, None, FakeLLM()))
    assert ai_service.tutor_reply("Câu hỏi", "Kết quả", []) == "Hãy kiểm tra dữ liệu."


@pytest.mark.parametrize("available", [True, False])
def test_review_without_rubric_marks_unavailable_verification(monkeypatch, available):
    from app import ai_service

    class FakeLLM:
        def with_structured_output(self, schema):
            class Chain:
                def invoke(self, prompt):
                    if schema.__name__ == "QuestionReview":
                        return schema(checks=[{"question_id": 1, "status": "met", "feedback": "Phân tích rõ.", "suggestion": "Bổ sung giới hạn."}])
                    return schema(feedback="Bài có insight.", suggestion="Kiểm tra bằng chứng.", quality="good")
            return Chain()

    def evidence(*args):
        if not available:
            raise RuntimeError("Dataset verification unavailable")
        return "Đã kiểm tra tổng bằng 60.", []

    monkeypatch.setattr(ai_service, "_load_graph", lambda: (None, None, FakeLLM()))
    monkeypatch.setattr(ai_service, "run_graph", evidence)
    result = ai_service.review_answers({"questions": [{"question_id": 1, "question_order": 1, "question_text": "Insight là gì?", "answer_markdown": "Có tổng 60."}]}, [], [], "", 1)
    assert result["checks"][0]["verification_available"] is available
    assert result["checks"][0]["status"] == ("met" if available else "partial")
    assert result["overall"]["quality"] == ("good" if available else "insufficient_evidence")
