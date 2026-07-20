from flask import Blueprint, jsonify, session
from util.file_helper import FileHelper

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

@dashboard_bp.route("", methods=["GET"])
def get_dashboard():

    if "employee_id" not in session:
        return jsonify({
            "success":False
        }),401

    role = session.get("role")

    employees = FileHelper.read_all(
        "employees"
    )

    tasks = FileHelper.read_all(
        "tasks"
    )

    projects = FileHelper.read_all(
        "projects"
    )

    leaves = FileHelper.read_all(
        "leaves"
    )

    attendance = FileHelper.read_all(
        "attendance"
    )

    # ===================
    # ADMIN
    # ===================

    if role == "admin":

        todo = len(
            [t for t in tasks
             if t["status"]=="todo"]
        )

        doing = len(
            [t for t in tasks
             if t["status"]=="doing"]
        )

        done = len(
            [t for t in tasks
             if t["status"]=="done"]
        )

        return jsonify({

            "role":"admin",

            "employees":
            len(employees),

            "projects":
            len(projects),

            "tasks":
            len(tasks),

            "pending_leave":
            len(
                [
                    l for l in leaves
                    if l["status"]=="pending"
                ]
            ),

            "task_chart":{

                "todo":todo,
                "doing":doing,
                "done":done

            }
        })

    # ===================
    # USER
    # ===================

    user_tasks = [

        t for t in tasks

        if int(
            t["assignee_id"]
        ) == int(
            session["employee_id"]
        )
    ]

    return jsonify({

        "role":"user",

        "my_tasks":
        len(user_tasks),

        "done":

        len([
            t for t in user_tasks
            if t["status"]=="done"
        ]),

        "attendance":

        len([
            a for a in attendance
            if int(
                a["employee_id"]
            ) == int(
                session["employee_id"]
            )
        ]),

        "leave":

        len([
            l for l in leaves
            if int(
                l["employee_id"]
            ) == int(
                session["employee_id"]
            )
        ])
    })