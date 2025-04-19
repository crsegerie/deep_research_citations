This script allows you to change the formatting of Gemini Deep research

Steps
- Run deep research --> to gdoc -> Copy paste to notion
- Ask gemini 2.5 pro to perform the action X
- Copy paste the result in input_body.md
- Copy paste the sources in input_sources.
- Run the script






Action X: 
    # ask gemini 2.5 pro to add a X in front of all the sources numbers (that are not numbers in themselves)
    prompt = f"""
    recopy entirely the following text by adding an X just before all the numbers that are representing sources.

    For example "AI Safety Support Links 272" should become "AI Safety Support Links X272"

    but "AI Management Systems (e.g., ISO 42001)" should remain "AI Management Systems (e.g., ISO 42001)"


    {text}
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel()
    response = model.generate_content(prompt)
    text = response.text