def count_tokens(text: str) -> int:
    """
    Roughly estimates the number of tokens in a text string (char count / 4).
    
    Input:
        text (str): Input text.
    
    Output:
        int: Estimated token count.
    """
    return len(text) // 4
