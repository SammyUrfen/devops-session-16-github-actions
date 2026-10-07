from flask import Flask, jsonify, request

from app.calculator import add, divide, multiply, subtract

app = Flask(__name__)
OPS = {"add": add, "subtract": subtract, "multiply": multiply, "divide": divide}


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/<op>")
def calc(op):
    if op not in OPS:
        return jsonify(error=f"unknown operation: {op}"), 404
    try:
        a = float(request.args["a"])
        b = float(request.args["b"])
        return jsonify(result=OPS[op](a, b))
    except (KeyError, ValueError) as e:
        return jsonify(error=str(e)), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
