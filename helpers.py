from flask import redirect, session, render_template

from functools import wraps

# Requires login through route decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Error page with different outputs depending on the error code input
def error(message, code=""):
    return render_template("error.html", message=message, code=code)

# Converts .fetchall() sqlite3 result to printable dictionary result
def rowput(rows):
    return [dict(row) for row in rows]

# Taking an input of purchase
def datalyze(purchases):
    category = {
        "transportation": 0,
        "recreation": 0,
        "personal": 0,
        "groceries": 0
    }
    method = {
        "cash": 0,
        "credit": 0,
        "debit": 0
    }

    for i in range(len(purchases)):
        category[purchases[i]["category"]] += purchases[i]["amount"]
        method[purchases[i]["method"]] += purchases[i]["amount"]

    categoryChart = {
        "legend": "Category Data",
        "labels": category.keys(),
        "values": category.values()
    }
    methodChart = {
        "legend": "Method Data",
        "labels": method.keys(),
        "values": method.values()
    }

    return categoryChart, methodChart