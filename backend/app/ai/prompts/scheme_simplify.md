Translate this Indian government scheme information into {{language_name}} for people with little schooling.

Rules:
- Use very simple words, like for a class-6 student. Short sentences.
- Keep the meaning exactly. Do not add or remove eligibility conditions, benefits or steps.
- Keep all numbers, ₹ amounts, dates, ages, URLs and website names exactly as they are. Write digits as 0-9.
- Translate every part, including step titles and document names (for example "Aadhaar card" -> the {{language_name}} words for it). Only button or menu names shown on a website (like 'New Farmer Registration') may stay in English.
- Keep scheme short names and acronyms (PM-KISAN, PMJJBY, e-KYC, CSC, Aadhaar) recognisable; you may add the local name in brackets.
- Return the same JSON structure and the same keys. Translate only the values. Keep the same number of steps and documents, in the same order. Keep every key in rule_explanations.

Input JSON:
{{content_json}}

Return JSON only with keys: name, benefit_summary, description, steps (list of {"title", "description"}), documents (list of strings), rule_explanations (object).
