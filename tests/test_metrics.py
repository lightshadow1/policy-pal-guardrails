from conftest import row

from ppguard.labels import Decision
from ppguard.metrics import confusion, summary


def test_summary_false_refusal_and_pairs():
    rows = [row("a", "in_scope", covered=True, pair_id="k"), row("b", "not_allowed", topic="legal", pair_id="k"),
            row("c", "in_scope", covered=False)]
    dec = {"a": Decision("in_scope"), "b": Decision("not_allowed", "medical"), "c": Decision("irrelevant")}
    s = summary(rows, dec, n_boot=50)
    assert s["false_refusal"] == 0.5 and s["false_refusal_uncovered"] == 1.0 and s["false_refusal_covered"] == 0.0
    assert s["pair_accuracy"] == 1.0 and s["topic_recall"]["legal"] == 1.0 and s["topic_exact"]["legal"] == 0.0


def test_confusion_counts():
    c = confusion(["in_scope", "in_scope", "ambiguous"], ["in_scope", "irrelevant", "in_scope"])
    assert c["in_scope"]["in_scope"] == 1 and c["in_scope"]["irrelevant"] == 1 and c["ambiguous"]["in_scope"] == 1
    assert c["not_allowed"]["not_allowed"] == 0


def test_summary_accuracy_and_macro_f1():
    rows = [row("a", "in_scope", covered=True), row("b", "irrelevant")]
    s = summary(rows, {"a": Decision("in_scope"), "b": Decision("in_scope")}, n_boot=50)
    assert s["accuracy"] == 0.5 and s["recall"]["in_scope"] == 1.0 and s["precision"]["in_scope"] == 0.5
    assert s["n"] == 2 and 0 <= s["accuracy_ci"][0] <= s["accuracy_ci"][1] <= 1
