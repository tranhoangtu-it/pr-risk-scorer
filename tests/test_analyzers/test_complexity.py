"""Tests for ComplexityAnalyzer."""


from pr_risk_scorer.analyzers.complexity import ComplexityAnalyzer
from pr_risk_scorer.models import FileChange, PRData


def test_complexity_nested_code():
    """Test detection of deep nesting."""
    patch = """@@ -1,3 +1,10 @@
+def process_data(items):
+    for item in items:
+        if item.valid:
+            for sub in item.children:
+                if sub.active:
+                    if sub.value > 0:
+                        result.append(sub)
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=1,
        title="Nested code",
        author="developer",
        files=[
            FileChange(filename="src/processor.py", additions=7, deletions=0, patch=patch),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "complexity"
    assert result.confidence == 0.7
    assert result.details["max_nesting"] >= 4  # Deep nesting detected
    assert result.details["loops"] >= 2  # Two for loops
    assert result.details["conditionals"] >= 3  # Three if statements
    assert result.score > 0


def test_conditional_complexity():
    """Test detection of high conditional complexity."""
    patch = """@@ -1,3 +1,15 @@
+if condition1:
+    handle_case1()
+elif condition2:
+    handle_case2()
+elif condition3:
+    handle_case3()
+else:
+    handle_default()
+
+if another_check:
+    process()
+elif fallback:
+    recover()
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=2,
        title="Complex conditionals",
        author="developer",
        files=[
            FileChange(filename="src/logic.py", additions=12, deletions=0, patch=patch),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["conditionals"] >= 6  # Multiple if/elif/else
    assert result.score > 0


def test_long_lines():
    """Test detection of long lines."""
    long_line = "x" * 150  # 150 character line
    patch = f"""@@ -1,3 +1,8 @@
+{long_line}
+another_long_line = "{'a' * 130}"
+third_long_line = "{'b' * 125}"
+fourth_long_line = "{'c' * 140}"
+fifth_long_line = "{'d' * 135}"
+short = "ok"
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=3,
        title="Long lines",
        author="developer",
        files=[
            FileChange(filename="src/data.py", additions=6, deletions=0, patch=patch),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["long_lines"] >= 5  # Five lines over 120 chars
    assert any("Long lines detected" in rec for rec in result.recommendations)


def test_score_bounds():
    """Test that scores are always within bounds."""
    # Empty PR
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=4,
        title="Empty PR",
        author="developer",
        files=[],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.score == 0  # No changes = no complexity

    # Highly complex PR
    complex_patch = """@@ -1,3 +1,30 @@
+def complex_function(data):
+    for item in data:
+        if item.type == "A":
+            for sub in item.children:
+                if sub.valid:
+                    for value in sub.values:
+                        if value > threshold:
+                            if value < max_threshold:
+                                process(value)
+        elif item.type == "B":
+            handle_b()
+        elif item.type == "C":
+            handle_c()
+        else:
+            default()
+    while processing:
+        if check():
+            continue
+        elif retry():
+            break
"""
    complex_pr = PRData(
        owner="test",
        repo="test-repo",
        number=5,
        title="Complex code",
        author="developer",
        files=[
            FileChange(
                filename="src/complex.py", additions=20, deletions=0, patch=complex_patch
            ),
        ],
    )

    result = analyzer.analyze(complex_pr)
    assert 0 <= result.score <= 100
    assert result.score > 30  # Should be high complexity


def test_no_patch_data():
    """Test handling of files without patch data."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=6,
        title="Binary files",
        author="developer",
        files=[
            FileChange(filename="image.png", additions=0, deletions=0, patch=None),
            FileChange(filename="data.bin", additions=0, deletions=0, patch=None),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.score == 0
    assert result.details["max_nesting"] == 0
    assert result.details["conditionals"] == 0
    assert result.details["loops"] == 0


def test_loop_detection():
    """Test detection of various loop types."""
    patch = """@@ -1,3 +1,10 @@
+for item in items:
+    process(item)
+
+while running:
+    if should_stop():
+        break
+
+for i in range(10):
+    calculate(i)
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=7,
        title="Loop heavy code",
        author="developer",
        files=[
            FileChange(filename="src/loops.py", additions=8, deletions=0, patch=patch),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["loops"] >= 3  # for, while, for
    assert result.score > 0


def test_recommendations():
    """Test that appropriate recommendations are generated."""
    # High nesting
    high_nesting = """@@ -1,3 +1,8 @@
+def nested():
+    if a:
+        if b:
+            if c:
+                if d:
+                    work()
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=8,
        title="Deep nesting",
        author="developer",
        files=[
            FileChange(filename="src/nested.py", additions=6, deletions=0, patch=high_nesting),
        ],
    )

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(pr_data)

    assert any("Deep nesting" in rec for rec in result.recommendations)


def test_high_conditional_recommendation():
    """Test recommendation triggers when conditionals >= 10."""
    lines = "\n".join(f"+if cond{i}:" for i in range(12))
    patch = f"@@ -1,3 +1,15 @@\n{lines}"
    pr_data = PRData(
        owner="test", repo="test-repo", number=9,
        title="Many conditionals", author="developer",
        files=[FileChange(filename="src/conds.py", additions=12, deletions=0, patch=patch)],
    )
    result = ComplexityAnalyzer().analyze(pr_data)
    assert result.details["conditionals"] >= 10
    assert any("High conditional complexity" in r for r in result.recommendations)


def test_high_loop_recommendation():
    """Test recommendation triggers when loops >= 5."""
    lines = "\n".join(f"+for i{j} in range({j}):" for j in range(6))
    patch = f"@@ -1,3 +1,8 @@\n{lines}"
    pr_data = PRData(
        owner="test", repo="test-repo", number=10,
        title="Many loops", author="developer",
        files=[FileChange(filename="src/loops2.py", additions=6, deletions=0, patch=patch)],
    )
    result = ComplexityAnalyzer().analyze(pr_data)
    assert result.details["loops"] >= 5
    assert any("Multiple loops" in r for r in result.recommendations)
