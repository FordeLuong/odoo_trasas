from . import models
from . import wizard


def _assign_outgoing_stages(env):
    """Migrate existing outgoing dispatch records: assign stage_id from old state values."""
    cr = env.cr

    mapping = {
        "draft": "outgoing_stage_draft",
        "waiting_approval": "outgoing_stage_waiting_approval",
        "approved": "outgoing_stage_approved",
        "to_promulgate": "outgoing_stage_to_promulgate",
        "processing": "outgoing_stage_processing",
        "released": "outgoing_stage_released",
        "sent": "outgoing_stage_sent",
        "done": "outgoing_stage_done",
        "cancel": "outgoing_stage_cancel",
    }

    for state_val, xmlid in mapping.items():
        stage = env.ref(f"trasas_dispatch_outgoing.{xmlid}", raise_if_not_found=False)
        if stage:
            cr.execute(
                """
                UPDATE trasas_dispatch_outgoing
                SET stage_id = %s
                WHERE (stage_id IS NULL) AND (state = %s)
                """,
                (stage.id, state_val),
            )

    # Catch remaining NULL → draft
    draft_stage = env.ref(
        "trasas_dispatch_outgoing.outgoing_stage_draft", raise_if_not_found=False
    )
    if draft_stage:
        cr.execute(
            """
            UPDATE trasas_dispatch_outgoing
            SET stage_id = %s
            WHERE stage_id IS NULL
            """,
            (draft_stage.id,),
        )
