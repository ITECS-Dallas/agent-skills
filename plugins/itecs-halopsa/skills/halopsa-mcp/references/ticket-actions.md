# Ticket actions

## Status and Start Work

For “mark In Progress,” read the exact ticket and its current status. If it is already In Progress, report its status and assignee. Otherwise, resolve the In Progress status ID with `halopsa.ticket_statuses.list` when unknown, then pass the expected current status to `halopsa.tickets.update_status`. Use an assignment tool only when the technician asks to change the assignee.

For an explicit Start Work request, pass the ticket's `last_update` as `expected_last_update` to `halopsa.ticket_actions.start_work`. It resolves the available native outcome. Halo's browser timer runs separately.

## Native ticket closure

For a technician’s Resolve or Close request, use the current ticket’s `last_update` as `expected_last_update` in `halopsa.ticket_actions.resolve`. Supply the work-completed `note` and the technician’s `email_user` choice. If the choice is absent, ask whether to email the user and wait for the answer. Set `close: true` for an explicit Close request. Halo uses the exact Close action when available and follows native Resolve when the current workflow only offers Resolve. Supply `resolution_category` if the action requires it and the ticket does not have one. Execute the authorized action with `confirm: true`.

If the ticket’s current workflow step has no Resolve or Close action, identify the applicable workflow step and its available actions. Report what Halo requires before closure.

Report the applied `outcome_name` and actual status from `operation.result.ticket_readback`. When `operation.result.pending_customer_confirmation` is true, report that the ticket is pending client confirmation. Use `action_readback` to verify the stored note and `email_user_recorded` for the action’s email evidence. Inbox delivery requires separate evidence. If the action outcome is uncertain, read back the ticket and its action before any retry.

## Screenshot attachment

Use the screenshot’s absolute local path with `halopsa.attachments.upload` on the exact ticket. PNG and JPEG are supported. A chat image without a file path needs to be saved as a local file first. If the app provided a readable path in a hidden folder, copy the screenshot bytes to a visible local folder and use that path. On Windows, Downloads is a visible folder when the screenshot is under a hidden AppData path.

Use the preview’s `context.file.sha256` as `expected_sha256` with `confirm: true`. The attachment is internal to the ticket. Check the verified attachment name and size in the upload readback. In HaloPSA, open the ticket’s Attachments tab and use the image’s Download Attachment command to open the file.

## Standalone email to the ticket contact

Use `halopsa.ticket_actions.send_email` with the exact ticket ID, current `last_update` as `expected_last_update`, and the requested subject and body. Leave `to` and `outcome_id` unset to use the ticket’s designated contact and its available Email User action. Follow the active workspace’s sender instructions when they specify a route. Preserve draft-only requests.

After sending, verify the recorded outbound action and recipient from readback. Check the receiving mailbox separately when delivery must be established. For a different recipient or workflow outcome, supply the explicit values and inspect the configured effects when needed.
