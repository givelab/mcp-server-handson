import pytest
from handler import dispatch_tool, handle_add


@pytest.mark.asyncio
async def test_add_positive():
    result = await handle_add(3, 4)
    assert result[0].text == "7"


@pytest.mark.asyncio
async def test_add_negative():
    result = await handle_add(-5, 3)
    assert result[0].text == "-2"


@pytest.mark.asyncio
async def test_add_float():
    result = await handle_add(1.5, 2.5)
    assert result[0].text == "4.0"


@pytest.mark.asyncio
async def test_unknown_tool():
    with pytest.raises(ValueError, match="Unknown tool"):
        await dispatch_tool("nonexistent", {})


@pytest.mark.asyncio
async def test_multiply():
    result = await dispatch_tool("multiply", {"a": 3, "b": 4})
    assert result[0].text == "12"


@pytest.mark.asyncio
async def test_divide():
    result = await dispatch_tool("divide", {"a": 10, "b": 4})
    assert result[0].text == "2.5"


@pytest.mark.asyncio
async def test_divide_by_zero():
    with pytest.raises(ValueError, match="ゼロ除算"):
        await dispatch_tool("divide", {"a": 5, "b": 0})
