import json

from portfolio_tracker.cli import main


def test_cli_invalid_ticker_returns_non_zero_and_error(capsys) -> None:
    exit_code = main(["TOOLONG", "--mock"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "invalid ticker" in captured.err.lower()
    assert captured.out == ""


def test_cli_mock_markdown_outputs_complete_memo_and_warning_flags(capsys) -> None:
    exit_code = main(["MSFT", "--mock"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# Investment Memo: MSFT" in captured.out
    assert "## Recommendation Summary" in captured.out
    assert "## Key Risks" in captured.out
    assert "This is not investment advice." in captured.out
    assert "Data warnings:" in captured.err
    assert "Sentiment data partially available" in captured.err


def test_cli_mock_json_outputs_raw_memo_json(capsys) -> None:
    exit_code = main(["MSFT", "--mock", "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ticker"] == "MSFT"
    assert payload["not_investment_advice_disclaimer"] == "This is not investment advice."
    assert isinstance(payload["key_risks"], list)
    assert "Data warnings:" in captured.err
