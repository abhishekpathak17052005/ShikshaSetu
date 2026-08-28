"""Seed question bank with MCQ and SCENARIO questions."""
from datetime import UTC, datetime

from pymongo.database import Database

from app.questions.repository import insert_many_questions


def _create_question(
    question_id: str,
    competency_code: str,
    question_type: str,
    question_text: str,
    options: list[str],
    correct_answer: str,
    difficulty: str,
    explanation: str = "",
    scenario_context: str | None = None,
    weight: float = 1.0,
) -> dict:
    """Create a question document."""
    now = datetime.now(UTC)
    return {
        "question_id": question_id,
        "competency_code": competency_code,
        "question_type": question_type,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty": difficulty,
        "explanation": explanation,
        "scenario_context": scenario_context,
        "weight": weight,
        "source": "phase2_seed",
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now,
    }


def seed_questions(database: Database) -> dict[str, int]:
    """Seed question bank with sample questions."""
    questions = []
    
    # ============================================================
    # TECH_PYTHON - 15 questions (10 MCQ + 5 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "PY001", "TECH_PYTHON", "MCQ", "EASY",
            "What does the 'def' keyword do in Python?",
            ["Deletes a function", "Defines a function", "Declares a variable", "Imports a module"],
            "B", "The 'def' keyword defines a function in Python."
        ),
        _create_question(
            "PY002", "TECH_PYTHON", "MCQ", "EASY",
            "Which of the following is a mutable data type?",
            ["Tuple", "String", "List", "Integer"],
            "C", "Lists are mutable and can be modified after creation."
        ),
        _create_question(
            "PY003", "TECH_PYTHON", "MCQ", "MEDIUM",
            "What will this code print?\nmy_list = [1, 2, 3]\nprint(my_list[1])",
            ["1", "2", "3", "[1, 2, 3]"],
            "B", "Python uses 0-based indexing, so [1] returns the second element."
        ),
        _create_question(
            "PY004", "TECH_PYTHON", "MCQ", "MEDIUM",
            "Which method removes an element from a list?",
            ["delete()", "remove()", "pop()", "Both B and C"],
            "D", "Both remove() and pop() can remove elements from a list."
        ),
        _create_question(
            "PY005", "TECH_PYTHON", "MCQ", "MEDIUM",
            "What is the output of: print(type([1, 2, 3]))",
            ["<class 'array'>", "<class 'list'>", "<class 'tuple'>", "<class 'set'>"],
            "B", "Lists are typed as <class 'list'> in Python."
        ),
        _create_question(
            "PY006", "TECH_PYTHON", "MCQ", "HARD",
            "What is the difference between == and 'is' in Python?",
            ["No difference", "== compares values, 'is' compares identity", "'is' compares values", "== checks type only"],
            "B", "== checks value equality while 'is' checks if they're the same object."
        ),
        _create_question(
            "PY007", "TECH_PYTHON", "MCQ", "HARD",
            "What does *args represent in a function definition?",
            ["Arguments by reference", "Variable number of positional arguments", "Keyword arguments", "Named parameters"],
            "B", "*args allows a function to accept a variable number of positional arguments."
        ),
        _create_question(
            "PY008", "TECH_PYTHON", "MCQ", "HARD",
            "Which of these is a correct way to create a list comprehension?",
            ["[x for x in range(10)]", "[x foreach x in range(10)]", "[x for x to 10]", "[x in range(10)]"],
            "A", "List comprehensions use 'for x in iterable' syntax."
        ),
        _create_question(
            "PY009", "TECH_PYTHON", "MCQ", "MEDIUM",
            "What is the result of 'hello'.upper()?",
            ["hello", "Hello", "HELLO", "hELLO"],
            "C", "The upper() method converts all characters to uppercase."
        ),
        _create_question(
            "PY010", "TECH_PYTHON", "MCQ", "EASY",
            "How do you add a comment in Python?",
            ["// This is a comment", "# This is a comment", "<!-- This is a comment -->", "' This is a comment"],
            "B", "Python uses # for single-line comments."
        ),
        # SCENARIO questions
        _create_question(
            "PYS001", "TECH_PYTHON", "SCENARIO", "EASY",
            "You need to create a list of numbers 1-10. Which approach is most Pythonic?",
            ["list(range(1, 11))", "for i in range(1, 10): my_list.append(i)", "my_list = [1,2,3,4,5,6,7,8,9,10]", "None of the above"],
            "A", "List comprehensions and range() are the most Pythonic approaches.",
            scenario_context="You are writing clean, maintainable Python code.",
            weight=1.5
        ),
        _create_question(
            "PYS002", "TECH_PYTHON", "SCENARIO", "MEDIUM",
            "Your function needs to handle an unknown number of arguments. What should you use?",
            ["Regular parameters", "*args for positional arguments", "**kwargs for keyword arguments", "Both B and C"],
            "D", "Use *args for variable positional arguments and **kwargs for keyword arguments.",
            scenario_context="You are designing a flexible function interface.",
            weight=1.5
        ),
        _create_question(
            "PYS003", "TECH_PYTHON", "SCENARIO", "MEDIUM",
            "You need to find all even numbers in a list of 1000 items efficiently. Best approach?",
            ["for loop with if statement", "filter() with lambda", "List comprehension", "All are equally good"],
            "C", "List comprehension is idiomatic Python and efficient.",
            scenario_context="You are optimizing a data filtering operation.",
            weight=1.5
        ),
        _create_question(
            "PYS004", "TECH_PYTHON", "SCENARIO", "HARD",
            "Your code has circular imports. How do you resolve this?",
            ["Import inside function", "Restructure modules", "Use lazy imports", "All of the above"],
            "D", "Circular imports can be resolved through various strategies.",
            scenario_context="You are debugging a complex module dependency issue.",
            weight=2.0
        ),
        _create_question(
            "PYS005", "TECH_PYTHON", "SCENARIO", "HARD",
            "You need to create a class with private attributes. What convention do you use?",
            ["Prefix with underscore", "Prefix with double underscore", "Both", "Neither"],
            "C", "Python uses underscore prefixes for privacy by convention.",
            scenario_context="You are designing a robust object-oriented system.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # TECH_SQL - 15 questions (10 MCQ + 5 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "SQL001", "TECH_SQL", "MCQ", "EASY",
            "What does SELECT do in SQL?",
            ["Inserts data", "Retrieves data", "Updates data", "Deletes data"],
            "B", "SELECT retrieves data from a database."
        ),
        _create_question(
            "SQL002", "TECH_SQL", "MCQ", "EASY",
            "Which statement creates a table?",
            ["CREATE TABLE", "NEW TABLE", "INSERT TABLE", "BUILD TABLE"],
            "A", "CREATE TABLE is the correct SQL statement."
        ),
        _create_question(
            "SQL003", "TECH_SQL", "MCQ", "MEDIUM",
            "What does PRIMARY KEY do?",
            ["Encrypts data", "Identifies each record uniquely", "Sorts records", "Compresses data"],
            "B", "PRIMARY KEY uniquely identifies each record in a table."
        ),
        _create_question(
            "SQL004", "TECH_SQL", "MCQ", "MEDIUM",
            "Which JOIN returns all matching records?",
            ["LEFT JOIN", "INNER JOIN", "OUTER JOIN", "CROSS JOIN"],
            "B", "INNER JOIN returns only matching records from both tables."
        ),
        _create_question(
            "SQL005", "TECH_SQL", "MCQ", "MEDIUM",
            "What does GROUP BY do?",
            ["Orders results", "Filters results", "Groups results by column", "Limits results"],
            "C", "GROUP BY groups rows by column values."
        ),
        _create_question(
            "SQL006", "TECH_SQL", "MCQ", "HARD",
            "What is a FOREIGN KEY?",
            ["A key that links tables", "A key that encrypts data", "A temporary key", "A deleted key"],
            "A", "FOREIGN KEY creates a link between tables."
        ),
        _create_question(
            "SQL007", "TECH_SQL", "MCQ", "HARD",
            "What does normalization do?",
            ["Makes data bigger", "Reduces redundancy and improves integrity", "Encrypts data", "Compresses data"],
            "B", "Normalization reduces redundancy and improves data integrity."
        ),
        _create_question(
            "SQL008", "TECH_SQL", "MCQ", "HARD",
            "What is the correct syntax for an INNER JOIN?",
            ["SELECT * FROM table1 JOIN table2 ON table1.id = table2.id", "SELECT * FROM table1 INNER ON table2", "SELECT * FROM table1 & table2", "SELECT * FROM table1 + table2"],
            "A", "INNER JOIN uses ON clause to specify the join condition."
        ),
        _create_question(
            "SQL009", "TECH_SQL", "MCQ", "MEDIUM",
            "What does HAVING clause do?",
            ["Filters individual rows", "Filters groups of rows", "Sorts rows", "Limits rows"],
            "B", "HAVING filters groups after GROUP BY aggregation."
        ),
        _create_question(
            "SQL010", "TECH_SQL", "MCQ", "EASY",
            "What does the WHERE clause do?",
            ["Sorts data", "Filters data", "Joins tables", "Counts rows"],
            "B", "WHERE filters rows based on conditions."
        ),
        # SCENARIO questions
        _create_question(
            "SQLS001", "TECH_SQL", "SCENARIO", "EASY",
            "You need to find all customers from 'USA'. Best approach?",
            ["SELECT * FROM customers WHERE country='USA'", "SELECT * FROM customers", "UPDATE customers SET country='USA'", "DELETE FROM customers WHERE country!='USA'"],
            "A", "Use WHERE clause to filter by country.",
            scenario_context="You need to query a customer database.",
            weight=1.5
        ),
        _create_question(
            "SQLS002", "TECH_SQL", "SCENARIO", "MEDIUM",
            "You have orders and customers tables. How do you get customer name with their orders?",
            ["SELECT * FROM orders", "SELECT * FROM customers, orders", "SELECT * FROM customers JOIN orders ON customers.id = orders.customer_id", "SELECT customers.name FROM orders"],
            "C", "Use JOIN to combine data from related tables.",
            scenario_context="You need to correlate data from multiple tables.",
            weight=1.5
        ),
        _create_question(
            "SQLS003", "TECH_SQL", "SCENARIO", "MEDIUM",
            "You need total sales per product. Which statement?",
            ["SELECT product, SUM(sales) FROM sales_data GROUP BY product", "SELECT SUM(sales) FROM sales_data", "SELECT product, sales FROM sales_data ORDER BY sales", "SELECT * FROM sales_data"],
            "A", "Use GROUP BY with aggregate functions.",
            scenario_context="You need to analyze sales by product.",
            weight=1.5
        ),
        _create_question(
            "SQLS004", "TECH_SQL", "SCENARIO", "HARD",
            "You need to find high-value customers (total purchases > $10,000). How?",
            ["SELECT customer FROM orders WHERE amount > 10000", "SELECT customer, SUM(amount) FROM orders GROUP BY customer HAVING SUM(amount) > 10000", "SELECT * FROM customers WHERE amount > 10000", "SELECT customer FROM orders GROUP BY customer"],
            "B", "Use GROUP BY with HAVING to filter aggregated results.",
            scenario_context="You need advanced filtering on aggregated data.",
            weight=2.0
        ),
        _create_question(
            "SQLS005", "TECH_SQL", "SCENARIO", "HARD",
            "You're designing a schema with users and posts. What's the relationship?",
            ["One user, one post", "One user can have many posts", "Many users, many posts (no relationship)", "Users and posts are the same table"],
            "B", "Users have a one-to-many relationship with posts.",
            scenario_context="You are designing a blog database schema.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # STAT_SAMPLING - 10 questions (8 MCQ + 2 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "STAT001", "STAT_SAMPLING", "MCQ", "EASY",
            "What is sampling?",
            ["Studying entire population", "Selecting subset from population", "Creating a hypothesis", "Rejecting data"],
            "B", "Sampling is selecting a subset from a population for study."
        ),
        _create_question(
            "STAT002", "STAT_SAMPLING", "MCQ", "EASY",
            "What is random sampling?",
            ["Choosing first items", "Choosing any items systematically", "Each item has equal chance of selection", "Choosing last items"],
            "C", "Random sampling gives each item an equal chance of selection."
        ),
        _create_question(
            "STAT003", "STAT_SAMPLING", "MCQ", "MEDIUM",
            "What is sample size?",
            ["Size of population", "Number of items in sample", "Total observations needed", "Number of variables"],
            "B", "Sample size is the number of items selected."
        ),
        _create_question(
            "STAT004", "STAT_SAMPLING", "MCQ", "MEDIUM",
            "What is sampling error?",
            ["Errors in data collection", "Difference between sample and population", "Calculation mistake", "Data entry error"],
            "B", "Sampling error is the difference between sample statistic and population parameter."
        ),
        _create_question(
            "STAT005", "STAT_SAMPLING", "MCQ", "MEDIUM",
            "What is stratified sampling?",
            ["Random selection", "Dividing population into groups then sampling", "Systematic selection", "Cluster selection"],
            "B", "Stratified sampling divides population into strata then samples each."
        ),
        _create_question(
            "STAT006", "STAT_SAMPLING", "MCQ", "HARD",
            "What does central limit theorem state?",
            ["All populations are normal", "Sample means are normally distributed", "Sample sizes must be large", "Samples must be random"],
            "B", "CLT states sample means approach normal distribution."
        ),
        _create_question(
            "STAT007", "STAT_SAMPLING", "MCQ", "HARD",
            "What is confidence interval?",
            ["Certainty in one value", "Range likely containing parameter", "Sample mean range", "Population range"],
            "B", "Confidence interval is a range likely containing the parameter."
        ),
        _create_question(
            "STAT008", "STAT_SAMPLING", "MCQ", "MEDIUM",
            "What increases sample representativeness?",
            ["Larger sample size", "Random selection", "Proper stratification", "All of above"],
            "D", "All factors improve representativeness."
        ),
        # SCENARIO questions
        _create_question(
            "STATS001", "STAT_SAMPLING", "SCENARIO", "MEDIUM",
            "Surveying 1000 people from 10M population. What's the sampling approach?",
            ["Census all 10M", "Random sample of 1000", "Convenience sample", "Sample first 1000 found"],
            "B", "Random sampling is appropriate for population estimates.",
            scenario_context="You are designing a national survey.",
            weight=1.5
        ),
        _create_question(
            "STATS002", "STAT_SAMPLING", "SCENARIO", "HARD",
            "Population has 3 income groups (equal size). Best sampling method?",
            ["Simple random", "Stratified random", "Cluster", "Systematic"],
            "B", "Stratified sampling ensures representation from each income group.",
            scenario_context="You need income diversity in your study.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # DIGOV_CYBERSECURITY - 13 questions (10 MCQ + 3 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "CYB001", "DIGOV_CYBERSECURITY", "MCQ", "EASY",
            "What is a firewall?",
            ["Computer hardware", "Network security barrier", "Software updater", "Internet service"],
            "B", "A firewall blocks unauthorized access."
        ),
        _create_question(
            "CYB002", "DIGOV_CYBERSECURITY", "MCQ", "EASY",
            "What is encryption?",
            ["Data deletion", "Data scrambling for security", "Data backup", "Data transfer"],
            "B", "Encryption converts data to unreadable form."
        ),
        _create_question(
            "CYB003", "DIGOV_CYBERSECURITY", "MCQ", "MEDIUM",
            "What is phishing?",
            ["Catching fish", "Email fraud to steal credentials", "Network intrusion", "Data backup"],
            "B", "Phishing is fraudulent email to obtain credentials."
        ),
        _create_question(
            "CYB004", "DIGOV_CYBERSECURITY", "MCQ", "MEDIUM",
            "What is a VPN?",
            ["Very Private Network", "Virtual Private Network", "Verified Public Network", "Visual Private Network"],
            "B", "VPN creates encrypted connection over internet."
        ),
        _create_question(
            "CYB005", "DIGOV_CYBERSECURITY", "MCQ", "MEDIUM",
            "What is multi-factor authentication?",
            ["Multiple passwords", "Using 2+ verification methods", "Changing password often", "Complex passwords"],
            "B", "MFA uses multiple verification methods."
        ),
        _create_question(
            "CYB006", "DIGOV_CYBERSECURITY", "MCQ", "HARD",
            "What is a zero-day vulnerability?",
            ["Vulnerability affecting 0 users", "Previously unknown security flaw", "Virus from year zero", "Account with zero access"],
            "B", "Zero-day is a previously unknown vulnerability."
        ),
        _create_question(
            "CYB007", "DIGOV_CYBERSECURITY", "MCQ", "HARD",
            "What does HTTPS provide?",
            ["Faster internet", "Encrypted web connection", "Better graphics", "Larger storage"],
            "B", "HTTPS encrypts data transmitted to/from websites."
        ),
        _create_question(
            "CYB008", "DIGOV_CYBERSECURITY", "MCQ", "MEDIUM",
            "What is ransomware?",
            ["Random software", "Malware that locks/encrypts files for payment", "Antivirus software", "Backup software"],
            "B", "Ransomware encrypts data and demands payment."
        ),
        _create_question(
            "CYB009", "DIGOV_CYBERSECURITY", "MCQ", "HARD",
            "What is the principle of least privilege?",
            ["Giving maximum permissions", "Granting minimum necessary permissions", "No permissions", "Equal permissions for all"],
            "B", "Least privilege limits permissions to minimum needed."
        ),
        _create_question(
            "CYB010", "DIGOV_CYBERSECURITY", "MCQ", "MEDIUM",
            "What is a password manager?",
            ["Person managing passwords", "Software securing passwords", "Password encryption tool", "Both B and C"],
            "D", "Password managers are software tools."
        ),
        # SCENARIO questions
        _create_question(
            "CYBS001", "DIGOV_CYBERSECURITY", "SCENARIO", "MEDIUM",
            "Employee receives email claiming to verify account. Likely?",
            ["Legitimate company email", "Phishing attempt", "IT department", "Password reset"],
            "B", "Such emails are typically phishing attempts.",
            scenario_context="You are training employees on security.",
            weight=1.5
        ),
        _create_question(
            "CYBS002", "DIGOV_CYBERSECURITY", "SCENARIO", "HARD",
            "Company discovered breach. First action?",
            ["Continue normal operations", "Isolate affected systems", "Notify public immediately", "Delete evidence"],
            "B", "Isolate systems to prevent spread.",
            scenario_context="You are managing a security incident.",
            weight=2.0
        ),
        _create_question(
            "CYBS003", "DIGOV_CYBERSECURITY", "SCENARIO", "HARD",
            "Which is LEAST secure password practice?",
            ["20-char random password", "Password = 'Password123'", "Unique per account", "Stored in password manager"],
            "B", "Simple, predictable passwords are insecure.",
            scenario_context="You are auditing password policies.",
            weight=1.5
        ),
    ])
    
    # ============================================================
    # BEH_LEADERSHIP - 13 questions (8 MCQ + 5 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "LEAD001", "BEH_LEADERSHIP", "MCQ", "EASY",
            "What is leadership?",
            ["Having authority", "Influencing others toward goals", "Giving orders", "Being promoted"],
            "B", "Leadership is influencing others toward objectives."
        ),
        _create_question(
            "LEAD002", "BEH_LEADERSHIP", "MCQ", "EASY",
            "What is emotional intelligence?",
            ["Intelligence level", "Understanding emotions in self and others", "Feeling emotional", "Expressing feelings"],
            "B", "EI is understanding and managing emotions."
        ),
        _create_question(
            "LEAD003", "BEH_LEADERSHIP", "MCQ", "MEDIUM",
            "What is servant leadership?",
            ["Serving your boss", "Leading by serving team needs", "Following orders", "Delegating everything"],
            "B", "Servant leadership prioritizes team needs."
        ),
        _create_question(
            "LEAD004", "BEH_LEADERSHIP", "MCQ", "MEDIUM",
            "What builds team trust?",
            ["Strict rules", "Consistency, transparency, competence", "Hierarchy", "Micromanagement"],
            "B", "Trust comes from consistency and transparency."
        ),
        _create_question(
            "LEAD005", "BEH_LEADERSHIP", "MCQ", "MEDIUM",
            "What is visionary leadership?",
            ["Having good eyesight", "Articulating inspiring future direction", "Planning details", "Following trends"],
            "B", "Visionary leadership communicates inspiring direction."
        ),
        _create_question(
            "LEAD006", "BEH_LEADERSHIP", "MCQ", "HARD",
            "How to handle conflict constructively?",
            ["Ignore it", "Listen, understand, find solutions", "Take sides", "Punish involved parties"],
            "B", "Constructive conflict involves listening and problem-solving."
        ),
        _create_question(
            "LEAD007", "BEH_LEADERSHIP", "MCQ", "HARD",
            "What is adaptive leadership?",
            ["Following established methods", "Responding flexibly to change", "Resisting change", "Doing nothing new"],
            "B", "Adaptive leadership adjusts to changing contexts."
        ),
        _create_question(
            "LEAD008", "BEH_LEADERSHIP", "MCQ", "MEDIUM",
            "What motivates diverse teams?",
            ["Only money", "Recognition, growth, purpose, autonomy", "Fear of failure", "Competition only"],
            "B", "Motivation factors are multifaceted."
        ),
        # SCENARIO questions
        _create_question(
            "LEADS001", "BEH_LEADERSHIP", "SCENARIO", "MEDIUM",
            "Team member underperforms. First step?",
            ["Fire immediately", "Understand root cause through discussion", "Give warning", "Reduce pay"],
            "B", "Understand the situation before action.",
            scenario_context="You are managing a performance issue.",
            weight=1.5
        ),
        _create_question(
            "LEADS002", "BEH_LEADERSHIP", "SCENARIO", "MEDIUM",
            "Two team members in conflict. Best approach?",
            ["Pick a side", "Listen to both, facilitate resolution", "Ignore it", "Separate them permanently"],
            "B", "Facilitate dialogue and resolution.",
            scenario_context="You are resolving team conflict.",
            weight=1.5
        ),
        _create_question(
            "LEADS003", "BEH_LEADERSHIP", "SCENARIO", "HARD",
            "Significant organizational change. How to lead?",
            ["Don't communicate", "Communicate vision, listen concerns, support transition", "Impose change", "Wait and see"],
            "B", "Transparent communication aids change management.",
            scenario_context="You are leading organizational change.",
            weight=2.0
        ),
        _create_question(
            "LEADS004", "BEH_LEADERSHIP", "SCENARIO", "HARD",
            "Star performer wants transfer. Best response?",
            ["Deny request", "Listen to concerns, explore development", "Give ultimatum", "Discourage"],
            "B", "Understand motivations; support growth.",
            scenario_context="You are retaining talent.",
            weight=2.0
        ),
        _create_question(
            "LEADS005", "BEH_LEADERSHIP", "SCENARIO", "HARD",
            "You realize you made a mistake affecting team. Next?",
            ["Hide the error", "Acknowledge, explain, correct course", "Blame someone", "Pretend nothing happened"],
            "B", "Accountability builds trust.",
            scenario_context="You are demonstrating integrity.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # BEH_COMMUNICATION - 11 questions (8 MCQ + 3 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "COM001", "BEH_COMMUNICATION", "MCQ", "EASY",
            "What is effective communication?",
            ["Talking a lot", "Conveying message clearly to be understood", "Using big words", "Writing long emails"],
            "B", "Effective communication ensures understanding."
        ),
        _create_question(
            "COM002", "BEH_COMMUNICATION", "MCQ", "EASY",
            "What is active listening?",
            ["Waiting to speak", "Fully concentrating and understanding", "Hearing words only", "Judging speaker"],
            "B", "Active listening involves full concentration."
        ),
        _create_question(
            "COM003", "BEH_COMMUNICATION", "MCQ", "MEDIUM",
            "What is non-verbal communication?",
            ["Not talking", "Body language, tone, gesture", "Writing only", "Emails"],
            "B", "Non-verbal includes body language and tone."
        ),
        _create_question(
            "COM004", "BEH_COMMUNICATION", "MCQ", "MEDIUM",
            "What is feedback?",
            ["Criticism", "Information about performance or impact", "Compliments only", "Negative only"],
            "B", "Feedback is information about impact/performance."
        ),
        _create_question(
            "COM005", "BEH_COMMUNICATION", "MCQ", "MEDIUM",
            "What improves team communication?",
            ["Avoiding meetings", "Regular interaction, clarity, openness", "Emails only", "Top-down only"],
            "B", "Regular, clear, open interaction improves communication."
        ),
        _create_question(
            "COM006", "BEH_COMMUNICATION", "MCQ", "HARD",
            "What is empathetic communication?",
            ["Agreeing with everything", "Understanding others' perspective", "Sympathy", "Being nice"],
            "B", "Empathy means understanding perspective."
        ),
        _create_question(
            "COM007", "BEH_COMMUNICATION", "MCQ", "HARD",
            "How to deliver difficult feedback?",
            ["Harshly and publicly", "Privately, specifically, constructively", "Via email", "Indirectly through gossip"],
            "B", "Difficult feedback is best delivered privately and constructively."
        ),
        _create_question(
            "COM008", "BEH_COMMUNICATION", "MCQ", "MEDIUM",
            "What blocks effective communication?",
            ["Nothing", "Assumptions, jargon, distractions", "Clarity", "Understanding"],
            "B", "Many factors block effective communication."
        ),
        # SCENARIO questions
        _create_question(
            "COMS001", "BEH_COMMUNICATION", "SCENARIO", "MEDIUM",
            "Presenting complex info to non-technical audience. Best approach?",
            ["Use technical jargon", "Simplify, use examples, avoid jargon", "Assume knowledge", "Use slides only"],
            "B", "Simplify for the audience.",
            scenario_context="You are presenting to stakeholders.",
            weight=1.5
        ),
        _create_question(
            "COMS002", "BEH_COMMUNICATION", "SCENARIO", "HARD",
            "Colleague misunderstood your message. What to do?",
            ["Blame them", "Clarify again, ask questions, confirm understanding", "Repeat exactly", "Get angry"],
            "B", "Clarify and confirm understanding.",
            scenario_context="You are resolving a miscommunication.",
            weight=1.5
        ),
        _create_question(
            "COMS003", "BEH_COMMUNICATION", "SCENARIO", "HARD",
            "Giving critical feedback to senior person. How?",
            ["Don't give it", "Professionally, privately, with examples", "Publicly to shame", "Indirectly"],
            "B", "Professionalism and privacy matter regardless of rank.",
            scenario_context="You are providing upward feedback.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # BEH_PROJECT_MANAGEMENT - 11 questions (8 MCQ + 3 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "PM001", "BEH_PROJECT_MANAGEMENT", "MCQ", "EASY",
            "What is a project?",
            ["Ongoing work", "Temporary effort to create unique result", "Regular task", "Job position"],
            "B", "Projects are temporary, unique efforts."
        ),
        _create_question(
            "PM002", "BEH_PROJECT_MANAGEMENT", "MCQ", "EASY",
            "What is project scope?",
            ["Budget", "Work included and excluded", "Timeline", "Team size"],
            "B", "Scope defines what's included/excluded."
        ),
        _create_question(
            "PM003", "BEH_PROJECT_MANAGEMENT", "MCQ", "MEDIUM",
            "What is a critical path?",
            ["Shortest route", "Sequence of tasks determining minimum duration", "Biggest expense", "Most important task"],
            "B", "Critical path determines project duration."
        ),
        _create_question(
            "PM004", "BEH_PROJECT_MANAGEMENT", "MCQ", "MEDIUM",
            "What is risk in project management?",
            ["Always bad", "Uncertain event with impact", "Budget overrun", "Schedule delay"],
            "B", "Risk is uncertain with potential impact."
        ),
        _create_question(
            "PM005", "BEH_PROJECT_MANAGEMENT", "MCQ", "MEDIUM",
            "What is a stakeholder?",
            ["Manager only", "Anyone affected by or affecting project", "Team lead", "Executive"],
            "B", "Stakeholders include anyone impacted."
        ),
        _create_question(
            "PM006", "BEH_PROJECT_MANAGEMENT", "MCQ", "HARD",
            "What controls project changes?",
            ["Nothing", "Change control process with review/approval", "Anyone can change", "Manager decides alone"],
            "B", "Formal change control manages modifications."
        ),
        _create_question(
            "PM007", "BEH_PROJECT_MANAGEMENT", "MCQ", "HARD",
            "How to close a project properly?",
            ["Just stop work", "Document learnings, archive, celebrate", "Ignore lessons", "Let it fade"],
            "B", "Proper closure includes documentation and learning."
        ),
        _create_question(
            "PM008", "BEH_PROJECT_MANAGEMENT", "MCQ", "MEDIUM",
            "What is slack or float?",
            ["Lazy team", "Extra time before schedule impact", "Spare budget", "Free resources"],
            "B", "Slack is delay buffer before impacting schedule."
        ),
        # SCENARIO questions
        _create_question(
            "PMS001", "BEH_PROJECT_MANAGEMENT", "SCENARIO", "MEDIUM",
            "Project behind schedule. Best action?",
            ["Work weekends indefinitely", "Assess cause, adjust plan, add resources if needed", "Ignore delays", "Cut corners"],
            "B", "Address root cause; adjust realistically.",
            scenario_context="You are managing schedule risk.",
            weight=1.5
        ),
        _create_question(
            "PMS002", "BEH_PROJECT_MANAGEMENT", "SCENARIO", "HARD",
            "Stakeholder demands scope change mid-project. Process?",
            ["Add immediately", "Evaluate impact, follow change control, adjust plan", "Refuse everything", "Ignore request"],
            "B", "Formal change control is essential.",
            scenario_context="You are managing scope creep.",
            weight=1.5
        ),
        _create_question(
            "PMS003", "BEH_PROJECT_MANAGEMENT", "SCENARIO", "HARD",
            "Key team member leaving mid-project. Response?",
            ["Panic", "Plan transition, onboard replacement, assess impact", "Redistribute work immediately", "Give up"],
            "B", "Managed transitions minimize impact.",
            scenario_context="You are managing resource risks.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # TECH_R - 11 questions (8 MCQ + 3 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "R001", "TECH_R", "MCQ", "EASY",
            "What does R do?",
            ["Creates graphics", "Statistical computing and data analysis", "Web development", "Mobile apps"],
            "B", "R is a language for statistical computing."
        ),
        _create_question(
            "R002", "TECH_R", "MCQ", "EASY",
            "What is a vector in R?",
            ["Graphic element", "One-dimensional array of data", "Force in physics", "Database field"],
            "B", "Vectors are R's basic data structure."
        ),
        _create_question(
            "R003", "TECH_R", "MCQ", "MEDIUM",
            "What does mean() calculate?",
            ["Hostile intent", "Average of values", "Median", "Most frequent value"],
            "B", "mean() calculates average."
        ),
        _create_question(
            "R004", "TECH_R", "MCQ", "MEDIUM",
            "What is a data frame?",
            ["Graphics frame", "Tabular data structure like spreadsheet", "Video frame", "Picture frame"],
            "B", "Data frames are R's table-like structure."
        ),
        _create_question(
            "R005", "TECH_R", "MCQ", "MEDIUM",
            "What does ggplot2 do?",
            ["Plotting functions", "Data visualization using grammar of graphics", "Statistical testing", "Data cleaning"],
            "B", "ggplot2 is a plotting package."
        ),
        _create_question(
            "R006", "TECH_R", "MCQ", "HARD",
            "How to create a function in R?",
            ["function <- code", "function = code", "func <- function() { code }", "Both B and C"],
            "C", "Use function() { } syntax."
        ),
        _create_question(
            "R007", "TECH_R", "MCQ", "HARD",
            "What is vectorization?",
            ["Graphics operation", "Operating on entire vectors without loops", "Vector graphics", "Drawing vectors"],
            "B", "Vectorization avoids loops for efficiency."
        ),
        _create_question(
            "R008", "TECH_R", "MCQ", "MEDIUM",
            "What does library() do?",
            ["Manages books", "Loads packages in R", "Stores variables", "Creates data"],
            "B", "library() loads R packages."
        ),
        # SCENARIO questions
        _create_question(
            "RS001", "TECH_R", "SCENARIO", "MEDIUM",
            "You have survey data in CSV. First step in R?",
            ["Plot immediately", "Read CSV with read.csv(), explore structure", "Run statistics", "Clean all data"],
            "B", "Load and explore data first.",
            scenario_context="You are starting data analysis.",
            weight=1.5
        ),
        _create_question(
            "RS002", "TECH_R", "SCENARIO", "HARD",
            "Need to visualize relationship between 2 variables. R approach?",
            ["Summary statistics", "Scatterplot with ggplot2", "Aggregate", "Table output"],
            "B", "Visualization reveals relationships.",
            scenario_context="You are exploratory data analysis.",
            weight=1.5
        ),
        _create_question(
            "RS003", "TECH_R", "SCENARIO", "HARD",
            "Testing hypothesis about population mean. R function?",
            ["mean()", "t.test()", "plot()", "summary()"],
            "B", "Use statistical tests for hypothesis testing.",
            scenario_context="You are conducting statistical tests.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # STAT_SURVEY_DESIGN - 10 questions (8 MCQ + 2 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "SURV001", "STAT_SURVEY_DESIGN", "MCQ", "EASY",
            "What is survey design?",
            ["Taking surveys", "Planning methodology for data collection", "Writing questions", "Analyzing results"],
            "B", "Survey design is planning the methodology."
        ),
        _create_question(
            "SURV002", "STAT_SURVEY_DESIGN", "MCQ", "EASY",
            "What is response bias?",
            ["Bias against response", "Systematic error in responses", "Refusing to respond", "Wrong answers"],
            "B", "Response bias is systematic error in answers."
        ),
        _create_question(
            "SURV003", "STAT_SURVEY_DESIGN", "MCQ", "MEDIUM",
            "What is survey validity?",
            ["Making it long", "Measuring what you intend to measure", "High response rate", "Complex questions"],
            "B", "Validity means measuring intended construct."
        ),
        _create_question(
            "SURV004", "STAT_SURVEY_DESIGN", "MCQ", "MEDIUM",
            "What is reliability in surveys?",
            ["Dependable internet", "Consistent measurement across time/people", "Quick response", "Detailed questions"],
            "B", "Reliability is consistency."
        ),
        _create_question(
            "SURV005", "STAT_SURVEY_DESIGN", "MCQ", "MEDIUM",
            "What are closed-ended questions?",
            ["Ended survey", "Predefined response options", "Open responses", "Yes/no only"],
            "B", "Closed-ended have predefined options."
        ),
        _create_question(
            "SURV006", "STAT_SURVEY_DESIGN", "MCQ", "HARD",
            "What is non-response bias?",
            ["Negative responses", "Systematic difference between responders/non-responders", "Bad responses", "No answers"],
            "B", "Non-response bias affects representativeness."
        ),
        _create_question(
            "SURV007", "STAT_SURVEY_DESIGN", "MCQ", "HARD",
            "What is survey precision?",
            ["Exact number", "Degree of certainty in estimate", "Sample size", "Response rate"],
            "B", "Precision relates to confidence in estimates."
        ),
        _create_question(
            "SURV008", "STAT_SURVEY_DESIGN", "MCQ", "MEDIUM",
            "How to minimize survey fatigue?",
            ["Longer surveys", "Keep concise, clear, purposeful", "Boring questions", "Repetitive questions"],
            "B", "Conciseness reduces fatigue."
        ),
        # SCENARIO questions
        _create_question(
            "SURVS001", "STAT_SURVEY_DESIGN", "SCENARIO", "MEDIUM",
            "Designing employee satisfaction survey. Key consideration?",
            ["Length only", "Question clarity, anonymity, representativeness", "Easy scoring", "Quick completion"],
            "B", "Multiple factors ensure valid results.",
            scenario_context="You are designing organizational survey.",
            weight=1.5
        ),
        _create_question(
            "SURVS002", "STAT_SURVEY_DESIGN", "SCENARIO", "HARD",
            "Low response rate to survey. Impact?",
            ["No problem", "May introduce non-response bias", "Results improved", "Smaller sample better"],
            "B", "Low response threatens representativeness.",
            scenario_context="You are assessing survey quality.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # DIGOV_DATA_PRIVACY - 13 questions (10 MCQ + 3 SCENARIO)
    # ============================================================
    questions.extend([
        _create_question(
            "PRIV001", "DIGOV_DATA_PRIVACY", "MCQ", "EASY",
            "What is data privacy?",
            ["Data storage", "Protecting personal information", "Data backup", "Data deletion"],
            "B", "Privacy protects personal information."
        ),
        _create_question(
            "PRIV002", "DIGOV_DATA_PRIVACY", "MCQ", "EASY",
            "What is GDPR?",
            ["Graphics processor", "Global Data Privacy Regulation", "General Data Protection Regulation", "B and C"],
            "D", "GDPR is European data protection law."
        ),
        _create_question(
            "PRIV003", "DIGOV_DATA_PRIVACY", "MCQ", "MEDIUM",
            "What is informed consent?",
            ["Agreeing without knowledge", "Understanding and agreeing to data use", "Required by law only", "Optional"],
            "B", "Consent requires understanding."
        ),
        _create_question(
            "PRIV004", "DIGOV_DATA_PRIVACY", "MCQ", "MEDIUM",
            "What is data minimization?",
            ["Delete all data", "Collecting only necessary data", "Storing minimal copies", "No storage"],
            "B", "Minimize data collection to necessity."
        ),
        _create_question(
            "PRIV005", "DIGOV_DATA_PRIVACY", "MCQ", "MEDIUM",
            "What is anonymization?",
            ["Hiding sender", "Removing personally identifiable information", "Encryption", "Deletion"],
            "B", "Anonymization removes identifying info."
        ),
        _create_question(
            "PRIV006", "DIGOV_DATA_PRIVACY", "MCQ", "HARD",
            "What is data controller?",
            ["Security officer", "Entity determining data processing purposes", "Data owner", "Data user"],
            "B", "Controller determines processing."
        ),
        _create_question(
            "PRIV007", "DIGOV_DATA_PRIVACY", "MCQ", "HARD",
            "What is right to be forgotten?",
            ["Forgetting passwords", "Right to request data deletion", "Losing data", "Memory issues"],
            "B", "Right to deletion is legal right."
        ),
        _create_question(
            "PRIV008", "DIGOV_DATA_PRIVACY", "MCQ", "MEDIUM",
            "How should passwords be stored?",
            ["Plain text", "Hashed", "Encrypted", "Both B and C"],
            "D", "Passwords need strong protection."
        ),
        _create_question(
            "PRIV009", "DIGOV_DATA_PRIVACY", "MCQ", "HARD",
            "What is data residency?",
            ["Where data physically stored", "Data type", "Data age", "Data size"],
            "A", "Data residency refers to physical location."
        ),
        _create_question(
            "PRIV010", "DIGOV_DATA_PRIVACY", "MCQ", "MEDIUM",
            "What triggers privacy breach notification?",
            ["No notification", "Unauthorized data access", "Authorized access only", "Manual access"],
            "B", "Unauthorized access triggers notification."
        ),
        # SCENARIO questions
        _create_question(
            "PRIVS001", "DIGOV_DATA_PRIVACY", "SCENARIO", "MEDIUM",
            "Employee requests their personal data. Your obligation?",
            ["Refuse", "Provide what's stored within timeframe", "Charge fee", "Ignore"],
            "B", "Right to access is legally protected."
            ,
            scenario_context="You are handling data access request.",
            weight=1.5
        ),
        _create_question(
            "PRIVS002", "DIGOV_DATA_PRIVACY", "SCENARIO", "HARD",
            "Security breach discovered. First action?",
            ["Hide it", "Notify affected individuals and authorities", "Ignore", "Delay notification"],
            "B", "Immediate notification is legal requirement.",
            scenario_context="You are responding to breach.",
            weight=2.0
        ),
        _create_question(
            "PRIVS003", "DIGOV_DATA_PRIVACY", "SCENARIO", "HARD",
            "Business wants all customer data in analytics. Legal?",
            ["Yes, always", "Need consent, minimize data, ensure protection", "Never", "Depends on profit"],
            "B", "Privacy principles must be followed.",
            scenario_context="You are balancing business and privacy.",
            weight=2.0
        ),
    ])
    
    # ============================================================
    # Insert all questions
    # ============================================================
    print(f"Seeding {len(questions)} questions...")
    inserted_ids = insert_many_questions(database, questions)
    
    # Count by competency
    competency_counts = {}
    for question in questions:
        comp = question["competency_code"]
        competency_counts[comp] = competency_counts.get(comp, 0) + 1
    
    return {
        "total_questions": len(questions),
        "inserted_ids": len(inserted_ids),
        "by_competency": competency_counts,
    }


if __name__ == "__main__":
    from app.core.database import initialize_database
    
    database = initialize_database()
    result = seed_questions(database)
    print(f"\n✓ Seeded {result['total_questions']} questions")
    print(f"✓ By competency: {result['by_competency']}")
