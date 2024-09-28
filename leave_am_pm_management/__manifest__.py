{
    "name": "Leave AM/PM Management",
    "version": "13.0.1.0.0",
    "category": "Human Resources",
    "summary": "Adds AM/PM selection to the leave request form in HR Management.",
    "author": "@JPSFT",
    "depends": ["hr_holidays", "hr_holidays_calendar"],
    "data": [
        "views/hr_leave_view.xml",
    ],
    "installable": True,
    "application": True,
    "description": """
Leave AM/PM Management
=======================

This module enhances the HR Management system in Odoo by allowing users to specify whether their leave request starts or ends in the morning (AM) or afternoon (PM). 

Key Features:
--------------
- **AM/PM Selection**: Adds two new selection fields for specifying AM/PM for both the start and end dates of leave requests.
- **Automatic Date Adjustment**: Automatically adjusts the `date_from` and `date_to` fields based on the AM/PM selection, ensuring that leave is recorded accurately.
- **User-Friendly Interface**: Integrates seamlessly with the existing leave request form, providing a straightforward user experience.

Installation:
-------------
1. Install the module through the Odoo apps interface.
2. Ensure that the `hr_holidays` module is already installed as it is a dependency.

Usage:
------
- Navigate to the Leave Request form in the HR Management section.
- Select the desired start and end dates for the leave.
- Choose AM or PM for both dates to specify the exact times.
- Submit the leave request for approval as usual.

This module is suitable for organizations that require precise control over leave timing, making it easier to manage employee leave requests effectively.
""",
}
