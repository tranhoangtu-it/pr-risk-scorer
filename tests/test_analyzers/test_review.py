"""Tests for ReviewAnalyzer."""


from pr_risk_scorer.analyzers.review import ReviewAnalyzer
from pr_risk_scorer.models import PRData, ReviewData


def test_no_reviews_high_risk():
    """Test that PRs with no reviews have high risk."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=1,
        title="Unreviewed PR",
        author="developer",
        reviews=[],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "review"
    assert result.score >= 70  # High risk for no reviews
    assert result.confidence == 0.9
    assert result.details["review_count"] == 0
    assert result.details["approval_count"] == 0
    assert any("No reviews yet" in rec for rec in result.recommendations)


def test_approved_reviews_low_risk():
    """Test that PRs with approvals have lower risk."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=2,
        title="Reviewed PR",
        author="developer",
        reviews=[
            ReviewData(
                reviewer="reviewer1",
                state="APPROVED",
                body="Looks good to me!",
            ),
            ReviewData(
                reviewer="reviewer2",
                state="APPROVED",
                body="LGTM, nice work",
            ),
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "review"
    assert result.score <= 30  # Low risk with 2 approvals
    assert result.details["review_count"] == 2
    assert result.details["approval_count"] == 2
    assert result.details["reviews_with_body"] == 2


def test_changes_requested_high_risk():
    """Test that outstanding change requests increase risk."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=3,
        title="PR needs changes",
        author="developer",
        reviews=[
            ReviewData(
                reviewer="reviewer1",
                state="CHANGES_REQUESTED",
                body="Please fix the tests",
            ),
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "review"
    assert result.score >= 75  # High risk with pending changes
    assert result.details["changes_requested"] == 1
    assert result.details["approval_count"] == 0
    assert any("Outstanding change requests" in rec for rec in result.recommendations)


def test_single_reviewer():
    """Test detection of single reviewer."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=4,
        title="Single review PR",
        author="developer",
        reviews=[
            ReviewData(
                reviewer="reviewer1",
                state="APPROVED",
                body="Approved",
            ),
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["review_count"] == 1
    assert result.details["approval_count"] == 1
    assert any("Single reviewer only" in rec for rec in result.recommendations)


def test_reviews_without_body():
    """Test detection of shallow reviews without comments."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=5,
        title="Shallow review PR",
        author="developer",
        reviews=[
            ReviewData(reviewer="reviewer1", state="APPROVED", body=""),
            ReviewData(reviewer="reviewer2", state="APPROVED", body=None),
            ReviewData(reviewer="reviewer3", state="APPROVED", body="   "),
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["review_count"] == 3
    assert result.details["reviews_with_body"] == 0
    assert any("lack detailed comments" in rec for rec in result.recommendations)


def test_score_bounds():
    """Test that scores are always within bounds."""
    # Maximum reviews (very low risk)
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=6,
        title="Well reviewed PR",
        author="developer",
        reviews=[
            ReviewData(reviewer=f"reviewer{i}", state="APPROVED", body="LGTM")
            for i in range(5)
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.score <= 20  # Very low risk

    # No reviews (high risk)
    empty_pr = PRData(
        owner="test",
        repo="test-repo",
        number=7,
        title="No reviews",
        author="developer",
        reviews=[],
    )

    result = analyzer.analyze(empty_pr)
    assert 0 <= result.score <= 100
    assert result.score >= 70  # High risk


def test_mixed_review_states():
    """Test PR with mixed review states."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=8,
        title="Mixed reviews",
        author="developer",
        reviews=[
            ReviewData(reviewer="reviewer1", state="APPROVED", body="Good"),
            ReviewData(reviewer="reviewer2", state="COMMENTED", body="Question"),
            ReviewData(
                reviewer="reviewer3",
                state="CHANGES_REQUESTED",
                body="Fix this",
            ),
        ],
    )

    analyzer = ReviewAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.details["review_count"] == 3
    assert result.details["approval_count"] == 1
    assert result.details["changes_requested"] == 1
    assert 0 <= result.score <= 100
