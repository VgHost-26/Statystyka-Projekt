from flask import Flask, jsonify
from flask_cors import CORS
from main import run_multiple_simulations, export_multiple_stats_to_csv
app = Flask(__name__)
CORS(app)


@app.route("/simulate", methods=["GET"])
def get_simulation_states():

    m_states, m_stats = run_multiple_simulations(100)
    export_multiple_stats_to_csv(m_stats, "simulation_stats.csv")

    return jsonify({"all_simulation_states": m_states, "all_stats": m_stats})


if __name__ == "__main__":
    app.run(debug=True)
