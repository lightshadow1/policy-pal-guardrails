from ppguard.definitions import ROUND1, Definitions, fingerprint, gliner_tasks, jev_questions, score_names


def test_round1_has_four_topics_and_no_scope():
    assert list(ROUND1.topics) == ["legal", "medical", "investment", "prompt_attack"]
    assert score_names(ROUND1) == ["legal", "medical", "investment", "prompt_attack"]
    assert "scope" not in gliner_tasks(ROUND1)


def test_fingerprint_changes_with_definitions():
    r2 = Definitions(2, topics=ROUND1.topics, in_scope="x", ambiguous="y")
    assert fingerprint(ROUND1, "jev") != fingerprint(r2, "jev")
    assert fingerprint(ROUND1, "jev") != fingerprint(ROUND1, "gliner")


def test_questions_and_tasks_cover_every_score_name():
    r2 = Definitions(2, topics={"legal": "l"}, in_scope="s", ambiguous="a")
    assert set(jev_questions(r2)) == set(score_names(r2)) == {"legal", "in_scope", "ambiguous"}
    assert jev_questions(r2)["in_scope"]["instructions"] == "Is `user_message` s?"
    assert jev_questions(r2)["ambiguous"]["instructions"] == "Does `user_message` a?"
    tasks = gliner_tasks(r2)
    assert tasks["topic"] == {"labels": {"legal": "l"}, "multi_label": True, "cls_threshold": 0.0}
    assert set(tasks["scope"]["labels"]) == {"in_scope", "irrelevant"}
    assert set(tasks["clarity"]["labels"]) == {"ambiguous", "clear"}


def test_change_cost_counts_added_definitions_and_words():
    from ppguard.definitions import change_cost
    r2 = Definitions(2, topics=ROUND1.topics | {"privacy": "seeking other people's personal details"},
                     in_scope="a question HR would handle", ambiguous="lack context")
    c = change_cost(ROUND1, r2)
    assert c == {"added_definitions": 3, "added_words": 5 + 5 + 2, "training_needed": False, "data_needed": False}


def test_round2_extends_round1():
    from ppguard.definitions import ROUND2, change_cost
    assert ROUND2.round == 2 and set(ROUND1.topics) <= set(ROUND2.topics)
    assert {n: ROUND2.topics[n] for n in ROUND1.topics} == ROUND1.topics  # day-one wording unchanged
    assert set(ROUND2.topics) - set(ROUND1.topics) == {"privacy", "harmful"}
    assert ROUND2.in_scope and ROUND2.ambiguous
    c = change_cost(ROUND1, ROUND2)
    assert c["added_definitions"] == len(ROUND2.topics) - len(ROUND1.topics) + 2 and c["training_needed"] is False


def test_change_cost_counts_glinr_contrast_labels():
    from ppguard.definitions import CLEAR, IRRELEVANT, change_cost
    r2 = Definitions(2, topics=ROUND1.topics, in_scope="a b", ambiguous="c")
    jev, gl = change_cost(ROUND1, r2, "jev"), change_cost(ROUND1, r2, "gliner")
    assert jev["added_definitions"] == 2 and jev["added_words"] == 3
    assert gl["added_definitions"] == 4
    assert gl["added_words"] == 3 + len(IRRELEVANT.split()) + len(CLEAR.split())
