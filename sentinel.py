"""Main application orchestrator for Page Sentinel.

Coordinates scheduled polling, state tracking, and alert dispatching.
"""

from __future__ import annotations

import argparse
import sys
import time

import config
import logger
import monitor
import notifiers
import storage


def print_banner() -> None:
    """Display startup configuration summary."""
    print()
    print(f"  {logger.Colors.BOLD}{logger.Colors.CYAN}🛡️  {config.APP_NAME} v{config.APP_VERSION}{logger.Colors.RESET}")
    logger.separator()

    display_url = config.TARGET_URL
    if len(display_url) > 60:
        display_url = display_url[:57] + "..."

    print(f"  {logger.Colors.BOLD}🎯 Target:{logger.Colors.RESET}    {display_url}")
    print(f"  {logger.Colors.BOLD}⏱️  Interval:{logger.Colors.RESET}  {config.CHECK_INTERVAL}s")

    channels = notifiers.get_enabled_channels()
    print(f"  {logger.Colors.BOLD}📡 Channels:{logger.Colors.RESET}  {', '.join(channels) if channels else 'None'}")

    if config.WATCHED_EXTENSIONS:
        ext_summary = ", ".join(config.WATCHED_EXTENSIONS)
        print(f"  {logger.Colors.BOLD}📎 Filter:{logger.Colors.RESET}    {ext_summary}")
    else:
        print(f"  {logger.Colors.BOLD}📎 Filter:{logger.Colors.RESET}    All Links")

    logger.separator()
    print()


def run_test_mode() -> int:
    """Send synthetic notification to verify external integration."""
    logger.info("Executing notification pipeline self-test...")
    result = notifiers.send_test()

    if result.succeeded:
        logger.success(f"Dispatched test alert to: {', '.join(result.succeeded)}")
    if result.failed:
        logger.error(f"Failed to dispatch test alert to: {', '.join(result.failed)}")

    return 0 if not result.failed else 1


def run_dry_run() -> int:
    """Perform a single inspection without saving state or sending alerts."""
    logger.info("Performing dry-run inspection...")
    result = monitor.fetch_and_parse(config.TARGET_URL)

    if result.error:
        logger.error(f"Dry-run failed: {result.error}")
        return 1

    state = storage.load_state()
    current_filenames = [f.filename for f in result.files]
    new_items = storage.get_new_files(current_filenames, state)

    logger.success(f"Total matching files found: {len(result.files)}")
    if new_items:
        logger.alert(f"Files that would trigger an alert ({len(new_items)}):")
        for name in new_items:
            logger.file_item(name)
    else:
        logger.info("No unrecorded files detected against current state.")

    return 0


def establish_initial_snapshot(state: dict) -> None:
    """Seed the baseline state on first run, retrying until server is reachable."""
    logger.info("Initializing baseline snapshot of target directory...")

    while True:
        result = monitor.fetch_and_parse(config.TARGET_URL)

        if result.error or result.status_code >= 400:
            logger.warning("Target unreachable during initialization. Retrying in 10s...")
            time.sleep(10)
            continue

        state["known_files"] = [f.filename for f in result.files]
        state["etag"] = result.etag
        state["last_modified"] = result.last_modified
        state["check_count"] = 1
        storage.save_state(state)

        logger.success(f"Baseline established with {len(result.files)} existing files.")
        print()
        break


def main_loop() -> None:
    """Execute continuous monitoring loop with drift compensation and delivery guarantees."""
    state = storage.load_state()

    if state.get("first_run", True):
        establish_initial_snapshot(state)
    else:
        known_count = len(state.get("known_files", []))
        logger.info(f"Loaded existing state: {known_count} files known.")
        print()

    check_count = state.get("check_count", 0)

    try:
        while True:
            # Drift-compensated sleep: account for processing time
            # so checks stay evenly spaced regardless of how long each cycle takes
            next_check = time.monotonic() + config.CHECK_INTERVAL
            time.sleep(config.CHECK_INTERVAL)

            check_count += 1
            result = monitor.fetch_and_parse(
                config.TARGET_URL,
                cached_etag=state.get("etag"),
                cached_last_modified=state.get("last_modified"),
            )

            # 304 Not Modified: zero bytes changed
            if result.not_modified:
                logger.success(f"Check #{check_count} — [304 Not Modified] Server reports no change.")
                continue

            if result.error:
                logger.warning(f"Check #{check_count} — Scrape error: {result.error}")
                continue

            current_filenames = [f.filename for f in result.files]
            new_filenames = storage.get_new_files(current_filenames, state)

            if new_filenames:
                count = len(new_filenames)
                title = f"🚨 {count} New Document{'s' if count > 1 else ''} Detected!"
                message = f"Detected {count} new file(s) posted to the selection index."

                new_set = set(new_filenames)
                new_file_items = [f for f in result.files if f.filename in new_set]
                dispatch_res = notifiers.dispatch(title, message, new_file_items)

                # Ensure we don't mark files as seen if remote delivery failed
                has_external_notifiers = config.NTFY_ENABLED or config.DISCORD_ENABLED
                if has_external_notifiers and not dispatch_res.has_external_success:
                    logger.error(
                        "All external notification channels failed to deliver! "
                        "State will not advance to prevent permanently missed alerts."
                    )
                    continue

                if dispatch_res.succeeded:
                    recipients = ", ".join(n for n in dispatch_res.succeeded if n != "console")
                    if recipients:
                        logger.success(f"Alerts dispatched to: {recipients}")

                # Update state upon verified delivery
                state["known_files"] = current_filenames
                state["etag"] = result.etag
                state["last_modified"] = result.last_modified
                state["check_count"] = check_count
                storage.save_state(state)

            else:
                total_files = len(result.files)
                logger.success(f"Check #{check_count} — {total_files} files indexed, no additions.")

                # Update metadata
                state["etag"] = result.etag
                state["last_modified"] = result.last_modified
                state["check_count"] = check_count

                if check_count % 15 == 0:
                    storage.save_state(state)

            # Drift compensation: sleep only the remaining time to maintain cadence
            remaining = next_check - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print()
        logger.info("Process interrupted by user.")
        state["check_count"] = check_count
        storage.save_state(state)
        logger.success("State synchronized to disk. Exiting cleanly. 👋\n")
        sys.exit(0)


def main() -> None:
    logger.setup_logging()

    parser = argparse.ArgumentParser(
        description=f"{config.APP_NAME} — Automated web change monitor with push notifications"
    )
    parser.add_argument("--test", action="store_true", help="Send test alerts and exit")
    parser.add_argument("--dry-run", action="store_true", help="Perform single check without alerting")

    args = parser.parse_args()

    print_banner()

    if args.test:
        sys.exit(run_test_mode())
    elif args.dry_run:
        sys.exit(run_dry_run())
    else:
        main_loop()


if __name__ == "__main__":
    main()
