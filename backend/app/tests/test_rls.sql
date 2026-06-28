SELECT set_config('app.current_user_role', 'auditor', true);
SELECT * FROM analytics_outputs;
SELECT set_config('app.current_user_role', 'owner', true);
SELECT * FROM analytics_outputs;
