from flask import Flask, jsonify, request
from flask_cors import CORS
from main import run_multiple_simulations, export_multiple_stats_to_csv, SCENARIOS

app = Flask(__name__)
CORS(app)


@app.route("/simulate", methods=["GET"])
# def get_simulation_states():

#     m_states, m_stats = run_multiple_simulations(100)
#     export_multiple_stats_to_csv(m_stats, "simulation_stats.csv")

#     return jsonify({"all_simulation_states": m_states, "all_stats": m_stats})

def get_simulation_states():
    scenario = request.args.get("scenario", "mixed")
    if scenario not in SCENARIOS:
        return jsonify({"error": f"Nieznany scenariusz '{scenario}'"}), 400

    dispensers_config = SCENARIOS[scenario]

    m_states, m_stats = run_multiple_simulations(100, dispensers_config)
    export_multiple_stats_to_csv(m_stats, f"simulation_stats_{scenario}.csv")

    return jsonify({
        "scenario": scenario,
        "all_simulation_states": m_states,
        "all_stats": m_stats
    })


if __name__ == "__main__":
    app.run(debug=True)
