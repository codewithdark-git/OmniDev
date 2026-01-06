"""Unit tests for UI components."""

import pytest

from omnidev.cli.ui.components import (
    ActionBlock,
    ErrorPanel,
    Logo,
    ProgressIndicator,
    StatusBar,
    TipsPanel,
    WarningPanel,
)


class TestUIComponents:
    """Test cases for UI components."""

    def test_logo_renders(self) -> None:
        """Test logo rendering."""
        # Logo.render() should not raise
        Logo.render()

    def test_tips_panel(self) -> None:
        """Test tips panel."""
        tips = TipsPanel(["Test tip 1", "Test tip 2"])
        tips.render(collapsed=False)

    def test_action_block(self) -> None:
        """Test action block."""
        block = ActionBlock(
            action="Test action",
            content="print('hello')",
            language="python",
        )
        block.render()

    def test_status_bar(self) -> None:
        """Test status bar."""
        status = StatusBar(files_indexed=10, providers=2, mode="auto")
        status.render()

    def test_progress_indicator(self) -> None:
        """Test progress indicator."""
        with ProgressIndicator("Testing..."):
            pass

    def test_error_panel(self) -> None:
        """Test error panel."""
        error = Exception("Test error")
        panel = ErrorPanel(error)
        panel.render()

    def test_warning_panel(self) -> None:
        """Test warning panel."""
        panel = WarningPanel("Test warning")
        panel.render()

