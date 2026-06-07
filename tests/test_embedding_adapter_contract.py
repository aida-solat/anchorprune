"""Contract tests for the v0.3 embedding adapter interface."""

from anchorprune.embeddings import EmbeddingClient, HashEmbeddingClient, cosine_similarity


def test_hash_embeddings_are_deterministic_and_fixed_dim():
    client = HashEmbeddingClient(dim=32)
    assert isinstance(client, EmbeddingClient)

    a1 = client.embed_text("require human approval")
    a2 = client.embed_text("require human approval")
    assert a1 == a2  # fully deterministic
    assert len(a1) == 32

    batch = client.embed_batch(["one", "two", "three"])
    assert len(batch) == 3
    assert all(len(v) == 32 for v in batch)


def test_hash_embeddings_similarity_self_is_one_and_differs_for_unrelated():
    client = HashEmbeddingClient(dim=64)
    v = client.embed_text("the policy requires approval")
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9

    unrelated = client.embed_text("zzz qqq vvv")
    assert cosine_similarity(v, unrelated) < cosine_similarity(v, v)


def test_empty_text_yields_zero_vector_without_error():
    client = HashEmbeddingClient(dim=8)
    v = client.embed_text("")
    assert v == [0.0] * 8
    assert cosine_similarity(v, v) == 0.0
