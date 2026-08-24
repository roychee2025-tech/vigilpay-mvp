def generate_coaching_question(turn_number=1, mode="multi"):

    if mode == "single":
        return (
            "Have you met the person who introduced this investment "
            "face-to-face, or have you only communicated online?"
        )

    questions = {
        1: (
            "Have you met the person who introduced this investment "
            "face-to-face, or have you only communicated online?"
        ),

        2: (
            "Were you told to keep this investment confidential "
            "from your family, friends or bank?"
        ),

        3: (
            "Have you successfully withdrawn any investment proceeds "
            "into your own bank account?"
        )
    }

    return questions.get(
        turn_number,
        "The coaching assessment is complete."
    )
