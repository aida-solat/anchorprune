"""Contract tests for the v0.3 LLM adapter interface."""

from anchorprune.llm import CallableLLM, EchoLLM, MockLLM
from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse, LLMResult


def test_mock_generate_returns_response_and_complete_maps_to_result():
    mock = MockLLM()
    response = mock.generate(LLMRequest(prompt="# Goal\nDo X\n\nrequires approval here"))
    assert isinstance(response, LLMResponse)
    assert response.text
    assert response.provider == "mock"
    assert response.input_tokens and response.output_tokens

    # The legacy wrapper must reconstruct an LLMResult, including proposed anchors
    # carried via response metadata.
    result = mock.complete("# Goal\nDo X\n\nrequires approval here")
    assert isinstance(result, LLMResult)
    assert result.proposed_anchor_texts == ["requires approval here"]


def test_all_default_adapters_satisfy_client_contract():
    for client in (MockLLM(), EchoLLM(), CallableLLM(lambda req: "ok:" + req.prompt)):
        assert isinstance(client, LLMClient)
        resp = client.generate(LLMRequest(prompt="hello"))
        assert isinstance(resp, LLMResponse)
        assert isinstance(resp.text, str) and resp.text
        # complete() works for free via the base wrapper.
        assert client.complete("hello").text


def test_callable_llm_rejects_non_string_output():
    bad = CallableLLM(lambda req: 123)  # type: ignore[arg-type,return-value]
    try:
        bad.generate(LLMRequest(prompt="x"))
    except TypeError:
        return
    raise AssertionError("CallableLLM should reject non-str output")
