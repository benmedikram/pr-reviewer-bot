## PR 94376: feat(upsampling) - Support upsampled error count with performance optimizations

### Reference issues
- **94376-R1** [Low / bug] In _set_sample_rate_from_error_sampling(), the check `if client_sample_rate:` treats 0.0 as falsy, so a sample_rate of 0.0 is silently skipped and never set on normalized_data.
- **94376-R2** [Low / data] Using Python’s built-in hash() to build cache keys is non-deterministic across processes (hash randomization), so keys won’t match across workers and invalidate_upsampling_cache may fail to delete them. Use a deterministic serialization of project_ids for the cache key.
- **94376-R3** [Medium / bug] The upsampling eligibility check passes the outer dataset instead of the actual dataset used by scoped_dataset. In paths where the query ultimately runs against discover (e.g., dashboard split) while the original dataset is metrics, upsampling may be skipped even when all projects are allowlisted.

### Bot findings
- **#1** `pyproject.toml:180` [changelog] Missing entry in CHANGES.md for the newly added public helper module error_upsampling.
- **#2** `src/sentry/api/endpoints/organization_events_stats.py:218` [changelog] User-visible behavior change (error upsampling) added without a corresponding entry in CHANGES.md
- **#3** `src/sentry/search/events/datasets/discover.py:1041` [changelog] Missing CHANGES.md entry for new public function 'upsampled_count'.
- **#4** `src/sentry/testutils/factories.py:351` [bare-except] Bare except Exception hides errors; consider catching specific exceptions.
- **#5** `src/sentry/testutils/factories.py:356` [bare-except] Bare except Exception hides errors; consider catching specific exceptions.

## PR 67876: GitHub OAuth Security Enhancement

### Reference issues
- **67876-R1** [Medium / bug] Null reference if github_authenticated_user state is missing
- **67876-R2** [Medium / security] OAuth state uses pipeline.signature (static) instead of a per-request random value
- **67876-R3** [High / bug] The code attempts to access integration.metadata[sender][login] without checking for the existence of the sender key. This causes a KeyError for integrations where the sender metadata was not set during creation

### Bot findings
- **#6** `src/sentry/web/frontend/pipeline_advancer.py:41` [changelog] User-visible behavior change: reduced FORWARD_INSTALL_FOR list to only "github" without updating CHANGES.md
- **#7** `tests/sentry/integrations/github/test_integration.py:116` [secret] Hard-coded secret token found in test code.

## PR 93824: Span Buffer Multiprocess Enhancement with Health Monitoring

### Reference issues
- **93824-R1** [Medium / bug] In the SpanFlusher flush loop, metric tags inconsistently use 'shard' (e.g., in spans.buffer.flusher.produce and spans.buffer.segment_size_bytes) and 'shards' (in spans.buffer.flusher.wait_produce) for the same shard identifier value. This prevents correct metric aggregation across flush stages — dashboards and alerts filtering by tag 'shard' will miss data tagged as 'shards' and vice versa.
- **93824-R2** [Low / test_gap] The test_basic function in test_consumer.py uses a monkeypatched time.sleep that returns immediately, but then calls time.sleep(0.1) expecting it to actually wait.
- **93824-R3** [High / bug] Because flusher processes are created via multiprocessing.get_context('spawn').Process, they are instances of multiprocessing.context.SpawnProcess, which on POSIX is not a subclass of multiprocessing.Process, so this isinstance check will always be false and hung processes won't be killed here.
- **93824-R4** [Medium / test_gap] Sleep in test_consumer.py won’t actually wait because time.sleep was monkeypatched above; consider restoring sleep or using a different sync to ensure the flusher has time to process.
- **93824-R5** [Medium / concurrency] Breaking out of the loop when the deadline has elapsed can skip terminating remaining flusher processes, potentially leaving them running after shutdown; consider ensuring termination is attempted even if the deadline is exceeded.

### Bot findings
- **#8** `src/sentry/spans/consumers/process/flusher.py:65` [other] Potential division by zero: if max_processes is falsy, self.num_processes can be zero, causing i % self.num_processes to raise ZeroDivisionError.
- **#9** `src/sentry/consumers/__init__.py:433` [changelog] User-visible CLI option "--flusher-processes" added without a corresponding entry in CHANGES.md.
- **#10** `src/sentry/consumers/__init__.py:433` [docs] Documentation not updated for the new "--flusher-processes" option, which changes user-facing behavior.

## PR 77754: feat(ecosystem): Implement cross-system issue synchronization

### Reference issues
- **77754-R1** [Medium / concurrency] The AssignmentSource dataclass uses queued: datetime = timezone.now() as a default field value, which evaluates timezone.now() once at class definition time and shares that single datetime instance across all objects.
- **77754-R2** [Low / style] The method name has a typo: test_from_dict_inalid_data should be test_from_dict_invalid_data.
- **77754-R3** [Low / style] Method name says 'empty_array' but tests empty dict - consider renaming to 'test_from_dict_empty_dict' for clarity.
- **77754-R4** [Medium / bug] to_dict() returns a datetime for queued; if this dict is passed in task kwargs (e.g., via apply_async), JSON serialization may fail depending on the serializer, which can cause enqueue errors.

### Bot findings
- **#11** `src/sentry/integrations/mixins/issues.py:66` [signature-compat] Nit: public method signature of IssueBasicIntegration.should_sync changed; confirm backwards compatibility and deprecation handling.
- **#12** `src/sentry/integrations/mixins/issues.py:382` [signature-compat] Nit: public method signature of IssueSyncIntegration.should_sync changed; ensure existing callers handle the new optional parameter.
- **#13** `src/sentry/integrations/mixins/issues.py:416` [signature-compat] Nit: sync_status_outbound now accepts an optional assignment_source argument; verify backward compatibility and documentation updates.
- **#14** `src/sentry/models/groupassignee.py:138` [signature-compat] Nit: GroupAssignee.assign signature gained assignment_source parameter; confirm callers and documentation are updated accordingly.
- **#15** `src/sentry/models/groupassignee.py:207` [signature-compat] Nit: GroupAssignee.deassign signature now includes assignment_source; ensure existing usage remains compatible.
- **#16** `src/sentry/integrations/tasks/sync_assignee_outbound.py:34` [signature-compat] Nit: sync_assignee_outbound task added assignment_source_dict parameter; check that task callers provide the new argument where needed.
- **#17** `src/sentry/integrations/utils/sync.py:127` [signature-compat] Nit: sync_group_assignee_outbound now takes optional assignment_source; verify all internal calls are updated and compatibility is preserved.

## PR 80528: ref(crons): Reorganize incident creation / issue occurrence logic

### Reference issues
- **80528-R1** [High / bug] The function modifies the config variable to include display values but then returns the original monitor.config instead of the modified version.
- **80528-R2** [Low / perf] The code fetches MonitorCheckIn objects by ID when the required data already exists in previous_checkins. This creates an unnecessary database query.

### Bot findings
- **#18** `src/sentry/monitors/logic/incident_occurrence.py:130` [type-hint] Missing return type hint for public function get_failure_reason.
- **#19** `src/sentry/monitors/logic/incident_occurrence.py:159` [type-hint] Missing return type hint for public function get_monitor_environment_context.
- **#20** `src/sentry/monitors/logic/incident_occurrence.py:148` [other] Edge case: get_failure_reason fails when failed_checkins is empty, leading to an empty list passed to get_text_list which may raise an error.
- **#21** `src/sentry/monitors/logic/mark_failed.py:79` [changelog] User-visible behavior change without a corresponding entry in CHANGES.md

## PR 95633: feat(uptime): Add ability to use queues to manage parallelism

### Reference issues
- **95633-R1** [Low / style] The magic number 50 for max_wait is used repeatedly throughout the tests. Consider extracting this as a named constant to improve maintainability.
- **95633-R2** [Low / doc_defect] The test test_thread_queue_parallel_error_handling has a docstring that doesn't match the test implementation.

### Bot findings
- **#22** `src/sentry/consumers/__init__.py:121` [changelog] A new click.Choice value 'thread-queue-parallel' is added, introducing a new user-visible mode. Ensure this behavior change is recorded in CHANGES.md with the appropriate PR reference.
- **#23** `src/sentry/consumers/__init__.py:121` [docs] The addition of the 'thread-queue-parallel' mode changes the CLI's user-facing behavior but no documentation under docs/ appears to be updated. Add or update documentation accordingly.
- **#24** `src/sentry/remote_subscriptions/consumers/queue_consumer.py:144` [bare-except] Catching broad Exception without re‑raising can hide errors; consider handling specific exceptions or re‑raise after logging.
- **#25** `src/sentry/remote_subscriptions/consumers/result_consumer.py:108` [changelog] Missing entry in CHANGES.md for new 'thread-queue-parallel' mode added to public API
- **#26** `tests/sentry/uptime/consumers/test_results_consumer.py:1780` [syntax-error] Syntax error: function definition missing return type after '->'

## PR 80168: feat(workflow_engine): Add in hook for producing occurrences from the stateful detector

### Reference issues
- **80168-R1** [High / api] MetricAlertDetectorHandler inherits from StatefulDetectorHandler but only contains pass, failing to implement its required abstract methods: counter_names (property), get_dedupe_value(), get_group_key_values(), and build_occurrence_and_event_data(). This will cause a TypeError at runtime when the class is instantiated.
- **80168-R2** [Low / doc_defect] Docstring says this returns a list of DetectorEvaluationResult, but the method now returns a dict keyed by DetectorGroupKey. Consider updating the docstring to match the new return type.
- **80168-R3** [Medium / test_gap] Wrong value `6` passed for `group_2` occurrence — the data packet specifies `"group_2": 10`. Should be `10` to accurately reflect the test scenario, which will ensure the test produces the correct occurrence data.

### Bot findings
- **#27** `src/sentry/workflow_engine/processors/detector.py:49` [signature-compat] Changed return type of public function process_detectors; confirm backward compatibility is handled and deprecation is documented.
- **#28** `src/sentry/workflow_engine/processors/detector.py:49` [changelog] User-visible behavior change (return type) without a corresponding entry in CHANGES.md.

