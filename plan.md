1. **Analyze and Assess:** The vulnerability is that the dynamic loading of CORS origins from the environment can inadvertently include `*` (wildcard), allowing any origin to access the API. The fix is to explicitly reject `*` in the CORS configuration to prevent misconfigurations from silently exposing the API.
2. **Implement Fix:** Update `backend/api/main.py` to parse `CORS_ALLOWED_ORIGINS`, strip whitespace, and raise a `ValueError` if `*` is provided, preventing the app from starting in an insecure state.
3. **Verify Fix:** Write a test in `backend/api/tests/test_cors.py` to ensure that configuring `*` raises an error and valid origins are accepted. Run `pytest` to verify.
4. **Document Learning:** Document the security learning in `.jules/sentinel.md` following the Sentinel format.
5. **Pre-commit Checks:** Run `pre_commit_instructions` to verify all steps (formatting, linting, tests).
6. **Create Pull Request:** Create a PR with the required Sentinel format: "🛡️ Sentinel: [Severity] Fix [vulnerability]" with Severity, Vulnerability, Impact, Fix, and Verification details.
