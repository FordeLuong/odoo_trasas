from . import controllers
from . import models


def _assign_stages_to_existing(env):
    """Migrate existing dispatch records: assign stage_id from old state values."""
    cr = env.cr

    # Map old state values to stage XML IDs
    mapping = {
        "draft": "stage_draft",
        "processing": "stage_processing",
        "waiting_confirmation": "stage_waiting",
        "done": "stage_done",
        "cancel": "stage_cancel",
    }

    for state_val, xmlid in mapping.items():
        stage = env.ref(f"trasas_dispatch_management.{xmlid}", raise_if_not_found=False)
        if stage:
            cr.execute(
                """
                UPDATE trasas_dispatch_incoming
                SET stage_id = %s
                WHERE (stage_id IS NULL) AND (state = %s)
                """,
                (stage.id, state_val),
            )

    # Catch any remaining records with no stage → assign to draft
    draft_stage = env.ref(
        "trasas_dispatch_management.stage_draft", raise_if_not_found=False
    )
    if draft_stage:
        cr.execute(
            """
            UPDATE trasas_dispatch_incoming
            SET stage_id = %s
            WHERE stage_id IS NULL
            """,
            (draft_stage.id,),
        )
