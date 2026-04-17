TRANSPARENCY_PAYLOAD = {
    "product_name": "CricSense",
    "stance": {
        "summary": "CricSense is a cricket analytics app, not a guaranteed-winning fantasy service.",
        "principles": [
            "Recent form matters.",
            "Context matters.",
            "Instinct and pressure behavior matter.",
            "Users should apply their own judgment.",
        ],
    },
    "terms_summary": [
        "Outputs are analytical suggestions only.",
        "No result or winnings are guaranteed.",
        "Users remain responsible for any fantasy-entry decisions.",
        "Captain and vice-captain suggestions are guidance, not certainty.",
    ],
    "formula_summary": {
        "player_layers": [
            "stats layer",
            "context layer",
            "instinct layer",
        ],
        "runtime_inputs": [
            "venue",
            "squad",
            "pitch note",
            "dew",
            "rain chance",
            "toss winner",
            "toss decision",
        ],
        "final_runtime_score": "base_stats_score * 0.24 + match_context_score * 0.35 + instinct_score * 0.25 + involvement_score * 0.10 + competition_boost * 0.06",
        "upside_score": "instinct_score * 0.45 + match_context_score * 0.25 + attack_intent_score * 0.20 + instinct_over_base_bonus * 0.10",
    },
}
