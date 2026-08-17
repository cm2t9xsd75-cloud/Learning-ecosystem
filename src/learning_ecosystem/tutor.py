"""Tutor runtime — pedagogy and interaction. Does not redefine curriculum."""

from __future__ import annotations

from dataclasses import dataclass, field

from learning_ecosystem.enums import ConceptStatus, EventType, NodeType, PrerequisiteType, ScopeStatus
from learning_ecosystem.models import Concept, CurriculumNode
from learning_ecosystem.protocol import (
    DIRECT_INSTRUCTION_REQUESTS,
    FRUSTRATION_MARKERS,
    PERMISSION_YES,
    READY_STATUSES,
    ContextLabel,
    ScaffoldLevel,
    TutorMode,
)
from learning_ecosystem.recorder import LearningRecorder
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    CONCEPT_BULKIFICATION,
    CONCEPT_FLOW_BULK,
    CONCEPT_FLOW_VS_APEX,
    CONCEPT_GOVERNORS,
    CONCEPT_SOQL,
    CONCEPT_TRANSACTION,
    CURRICULUM_ID,
    NODE_BULKIFICATION,
    NODE_FLOW_BULK,
    NODE_FLOW_VS_APEX,
    NODE_GOVERNORS,
    NODE_SOQL,
    NODE_TRANSACTIONS,
    SESSION_NEXT_OBJECTIVE,
)

NODE_CONCEPT = {
    NODE_SOQL: CONCEPT_SOQL,
    NODE_BULKIFICATION: CONCEPT_BULKIFICATION,
    NODE_GOVERNORS: CONCEPT_GOVERNORS,
    NODE_TRANSACTIONS: CONCEPT_TRANSACTION,
    NODE_FLOW_VS_APEX: CONCEPT_FLOW_VS_APEX,
    NODE_FLOW_BULK: CONCEPT_FLOW_BULK,
}

PROMPTS: dict[str, list[str]] = {
    CONCEPT_FLOW_BULK: [
        "Fifty Account updates enter one save. A record-triggered Flow exists on Account. "
        "What happens to interviews and to database operations in that transaction?",
        "If each interview has its own $Record, what is and is not shared across those interviews?",
        "How would Get Records or Update Records behave if they run while several interviews are in the same transaction?",
    ],
    CONCEPT_BULKIFICATION: [
        "A trigger walks Trigger.new and queries inside the loop. What resource is scaling, and with what?",
        "If 200 records arrive, what would you change so platform operations do not grow with each record?",
    ],
    CONCEPT_GOVERNORS: [
        "A single query returns 400 rows. Which governor dimension was consumed, and which was not?",
        "Why does Salesforce cap query count separately from returned rows?",
    ],
    CONCEPT_TRANSACTION: [
        "A Flow and a trigger both run after the same save. Are they automatically in different transactions? Why or why not?",
    ],
    CONCEPT_SOQL: [
        "How would you query Contact names together with each Contact's Account name for high-revenue accounts?",
    ],
    CONCEPT_FLOW_VS_APEX: [
        "A requirement needs bulk-safe automation and synchronous completion. What would you use, and what requirement drove that choice?",
    ],
}

CONTEXT_FOR_CONCEPT = {
    CONCEPT_FLOW_BULK: ContextLabel.TRIGGER_RECORD,
    CONCEPT_BULKIFICATION: ContextLabel.ALL_RECORDS,
    CONCEPT_GOVERNORS: ContextLabel.SYNC_TRANSACTION,
    CONCEPT_TRANSACTION: ContextLabel.SYNC_TRANSACTION,
    CONCEPT_SOQL: ContextLabel.STANDALONE_QUERY,
    CONCEPT_FLOW_VS_APEX: ContextLabel.SYNC_TRANSACTION,
}


@dataclass
class TutorTurn:
    session_id: str
    learner_id: str
    mode: TutorMode
    scaffold_level: ScaffoldLevel
    message: str
    question: str | None
    context_label: ContextLabel
    context_reset: bool
    objective_node_id: str
    concept_id: str
    awaiting_permission: bool
    out_of_scope: bool
    revealed_answer: bool


@dataclass
class _WorkingState:
    session_id: str
    learner_id: str
    objective_node_id: str
    concept_id: str
    mode: TutorMode
    scaffold_level: ScaffoldLevel
    context_label: ContextLabel
    prompt_index: int = 0
    awaiting_permission: bool = False
    last_learner_text: str | None = None
    unknown_count: int = 0


@dataclass
class TutorRuntime:
    repo: LearningEcosystemRepository
    recorder: LearningRecorder = field(init=False)
    _state: dict[str, _WorkingState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.recorder = LearningRecorder(self.repo)

    def start_session(self, learner_id: str, session_id: str | None = None) -> TutorTurn:
        resume = self.repo.load_resume_state(learner_id)
        session = self.repo.start_session(
            learner_id=learner_id,
            curriculum_id=CURRICULUM_ID,
            session_id=session_id,
        )
        node, deferred_target = self._select_objective(
            learner_id, resume.next_recommended_objectives
        )
        concept_id = NODE_CONCEPT[node.id]
        fundamentals_ready = self._required_prereqs_ready(learner_id, node.id)
        mode = TutorMode.PROBLEM_BASED if fundamentals_ready else TutorMode.FUNDAMENTALS
        context = CONTEXT_FOR_CONCEPT[concept_id]
        working = _WorkingState(
            session_id=session.id,
            learner_id=learner_id,
            objective_node_id=node.id,
            concept_id=concept_id,
            mode=mode,
            scaffold_level=ScaffoldLevel.SOCRATIC_QUESTION,
            context_label=context,
        )
        self._state[session.id] = working
        self.repo.add_session_objective(
            session_id=session.id,
            curriculum_node_id=node.id,
            starting_status=self._status(learner_id, concept_id),
        )
        self.repo.record_event(
            session_id=session.id,
            event_type=EventType.CONCEPT_INTRODUCED,
            concept_id=concept_id,
            details={"objective_node_id": node.id, "mode": mode.value},
        )
        if deferred_target is not None:
            self.repo.record_event(
                session_id=session.id,
                event_type=EventType.PREREQUISITE_GAP,
                concept_id=concept_id,
                details={
                    "blocked_target": deferred_target.id,
                    "selected_prerequisite": node.id,
                },
            )
        question = self._question(working)
        mastered = [
            state.concept_id
            for state in resume.concept_states
            if state.status is ConceptStatus.MASTERED
        ]
        skip_note = ""
        if mastered:
            skip_note = (
                "Resuming from persisted learner state. Mastered concepts will not be retaught. "
            )
        message = (
            f"{skip_note}Current context: {context.value}. "
            f"Next objective: {node.title}."
        )
        return TutorTurn(
            session_id=session.id,
            learner_id=learner_id,
            mode=mode,
            scaffold_level=working.scaffold_level,
            message=message,
            question=question,
            context_label=context,
            context_reset=False,
            objective_node_id=node.id,
            concept_id=concept_id,
            awaiting_permission=False,
            out_of_scope=False,
            revealed_answer=False,
        )

    def respond(
        self,
        session_id: str,
        learner_text: str,
        *,
        frustrated: bool | None = None,
    ) -> TutorTurn:
        working = self._state[session_id]
        text = learner_text.strip()
        frustrated = self._is_frustrated(text, working) if frustrated is None else frustrated
        requested_di = self._requested_di(text)
        concept = self.repo.get_concept(working.concept_id)
        artifacts = self.repo.list_artifacts_for_concept(working.concept_id)

        if working.awaiting_permission:
            return self._handle_permission(working, text, concept)

        evaluation = self.recorder.evaluate(text, concept=concept, artifacts=artifacts)
        if evaluation.out_of_scope:
            self.recorder.persist(
                session_id=session_id,
                learner_id=working.learner_id,
                evaluation=evaluation,
                learner_text=text,
            )
            return self._out_of_scope_turn(working, text)

        self.recorder.persist(
            session_id=session_id,
            learner_id=working.learner_id,
            evaluation=evaluation,
            learner_text=text,
        )

        if frustrated and working.mode is TutorMode.PROBLEM_BASED and not requested_di:
            return self._offer_direct_instruction(working)

        if requested_di and working.mode is TutorMode.PROBLEM_BASED:
            return self._give_direct_instruction(working, concept, requested=True)

        if evaluation.error_class and evaluation.error_class.value == "misconception":
            working.scaffold_level = ScaffoldLevel.SOCRATIC_QUESTION
            question = self._narrow_question(working, evaluation.assessment)
            return self._turn(
                working,
                message=(
                    "That claim may rest on an assumption. I will not supply the answer yet. "
                    "One question:"
                ),
                question=question,
                revealed=False,
            )

        if frustrated:
            working.scaffold_level = min(
                ScaffoldLevel.CONCEPTUAL_HINT,
                ScaffoldLevel(working.scaffold_level + 1),
            )
            if working.scaffold_level is ScaffoldLevel.DIRECT_INSTRUCTION:
                working.scaffold_level = ScaffoldLevel.CONCEPTUAL_HINT
            return self._turn(
                working,
                message=self._scaffold_message(working, concept),
                question=self._question(working),
                revealed=False,
            )

        working.prompt_index += 1
        working.scaffold_level = ScaffoldLevel.SOCRATIC_QUESTION
        return self._turn(
            working,
            message="Stay with the same context unless I signal a reset. Next question:",
            question=self._question(working),
            revealed=False,
        )

    def close_session(
        self,
        session_id: str,
        *,
        summary: str,
        takeaways: list[str],
        unresolved_items: list[str] | None = None,
    ):
        working = self._state[session_id]
        next_objective = SESSION_NEXT_OBJECTIVE
        unresolved = unresolved_items or [
            "Flow interview state, collection scope, and cross-interview database bulkification"
        ]
        return self.repo.close_session(
            session_id,
            summary=summary,
            takeaways=takeaways,
            unresolved_items=unresolved,
            next_recommended_objectives=[next_objective, working.objective_node_id],
        )

    def _select_objective(
        self, learner_id: str, recommended: list[str]
    ) -> tuple[CurriculumNode, CurriculumNode | None]:
        target_id = NODE_FLOW_BULK
        for item in recommended:
            if item in NODE_CONCEPT:
                target_id = item
                break
        blocked = self._first_blocking_required_prereq(learner_id, target_id)
        target = self.repo.get_node(target_id)
        if blocked is not None:
            return blocked, target
        return target, None

    def _first_blocking_required_prereq(
        self, learner_id: str, node_id: str
    ) -> CurriculumNode | None:
        for prereq in self.repo.list_prerequisites(node_id):
            if prereq.relationship_type is not PrerequisiteType.REQUIRED:
                continue
            concept_id = NODE_CONCEPT.get(prereq.prerequisite_node_id)
            if concept_id and self._status(learner_id, concept_id).value in READY_STATUSES:
                continue
            deeper = self._first_blocking_required_prereq(
                learner_id, prereq.prerequisite_node_id
            )
            if deeper is not None:
                return deeper
            if concept_id:
                return self.repo.get_node(prereq.prerequisite_node_id)
        return None

    def _required_prereqs_ready(self, learner_id: str, node_id: str) -> bool:
        return self._first_blocking_required_prereq(learner_id, node_id) is None

    def _status(self, learner_id: str, concept_id: str) -> ConceptStatus:
        state = self.repo.get_concept_state(learner_id, concept_id)
        return state.status if state else ConceptStatus.NOT_STARTED

    def _question(self, working: _WorkingState) -> str:
        prompts = PROMPTS[working.concept_id]
        return prompts[min(working.prompt_index, len(prompts) - 1)]

    def _narrow_question(self, working: _WorkingState, assessment: str) -> str:
        if "bulkif" in assessment.lower() or "automatically" in assessment.lower():
            return (
                "If Apex 'has bulkification built in', what happens when a developer "
                "puts SOQL or DML inside a loop over Trigger.new?"
            )
        if "150" in assessment or "query count" in assessment.lower():
            return (
                "A query that returns 400 rows still executed once. Which limit is the "
                "query-count limit measuring?"
            )
        return self._question(working)

    def _is_frustrated(self, text: str, working: _WorkingState) -> bool:
        lowered = text.lower()
        if any(marker in lowered for marker in FRUSTRATION_MARKERS):
            working.unknown_count += 1
            return True
        if working.last_learner_text and working.last_learner_text.lower() == lowered:
            working.unknown_count += 1
            return True
        working.last_learner_text = text
        return working.unknown_count >= 2

    def _requested_di(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in DIRECT_INSTRUCTION_REQUESTS)

    def _offer_direct_instruction(self, working: _WorkingState) -> TutorTurn:
        working.awaiting_permission = True
        working.mode = TutorMode.AWAITING_PERMISSION
        self.repo.record_event(
            session_id=working.session_id,
            event_type=EventType.FRUSTRATION_DETECTED,
            concept_id=working.concept_id,
            details={"action": "offer_direct_instruction"},
        )
        return self._turn(
            working,
            message=(
                "This is feeling heavy, so I will reduce the load. I can give a short "
                "direct explanation, but I need your permission before switching out of "
                "application mode. Would you like that?"
            ),
            question=None,
            revealed=False,
        )

    def _handle_permission(
        self, working: _WorkingState, text: str, concept: Concept
    ) -> TutorTurn:
        working.awaiting_permission = False
        if text.lower().strip() in PERMISSION_YES or text.lower().startswith("yes"):
            return self._give_direct_instruction(working, concept, requested=False)
        working.mode = TutorMode.PROBLEM_BASED
        working.scaffold_level = ScaffoldLevel.CLARIFICATION
        return self._turn(
            working,
            message="Staying in Socratic/application mode. Smaller question:",
            question=self._question(working),
            revealed=False,
        )

    def _give_direct_instruction(
        self, working: _WorkingState, concept: Concept, *, requested: bool
    ) -> TutorTurn:
        if requested:
            self.repo.record_event(
                session_id=working.session_id,
                event_type=EventType.DIRECT_INSTRUCTION_REQUESTED,
                concept_id=working.concept_id,
            )
        working.mode = TutorMode.DIRECT_INSTRUCTION
        working.scaffold_level = ScaffoldLevel.DIRECT_INSTRUCTION
        instruction = concept.definition
        working.mode = TutorMode.SOCRATIC
        working.scaffold_level = ScaffoldLevel.SOCRATIC_QUESTION
        working.prompt_index = min(working.prompt_index + 1, 2)
        return self._turn(
            working,
            message=(
                f"Direct instruction (then we return to Socratic): {instruction} "
                "Now apply it in your own words."
            ),
            question=self._question(working),
            revealed=True,
        )

    def _out_of_scope_turn(self, working: _WorkingState, text: str) -> TutorTurn:
        oos = [
            node
            for node in self.repo.list_nodes(CURRICULUM_ID, scope_status=ScopeStatus.OUT_OF_SCOPE)
            if node.node_type is NodeType.FUNDAMENTAL
        ]
        titles = ", ".join(node.title for node in oos[:3])
        return self._turn(
            working,
            message=(
                "OUT_OF_SCOPE_DEPENDENCY: that topic is not in the bounded PD1 "
                f"Process Automation & Logic knowledge base ({titles}, …). "
                "I will not add it as a required fundamental. Returning to the authorized objective."
            ),
            question=self._question(working),
            revealed=False,
            out_of_scope=True,
        )

    def _scaffold_message(self, working: _WorkingState, concept: Concept) -> str:
        if working.scaffold_level is ScaffoldLevel.CLARIFICATION:
            return "Let me clarify the question without answering it."
        if working.scaffold_level is ScaffoldLevel.DIRECTIONAL_HINT:
            return "Directional hint: think about what scales with records versus what scales with operations."
        if working.scaffold_level is ScaffoldLevel.CONCEPTUAL_HINT:
            return (
                "Conceptual hint: interview-local variables are not automatically "
                "one collection across interviews."
            )
        return "One Socratic question:"

    def _turn(
        self,
        working: _WorkingState,
        *,
        message: str,
        question: str | None,
        revealed: bool,
        out_of_scope: bool = False,
    ) -> TutorTurn:
        reset = False
        target_context = CONTEXT_FOR_CONCEPT[working.concept_id]
        if target_context is not working.context_label:
            reset = True
            message = (
                f"Context reset: leaving {working.context_label.value}, "
                f"entering {target_context.value}. {message}"
            )
            working.context_label = target_context
        return TutorTurn(
            session_id=working.session_id,
            learner_id=working.learner_id,
            mode=working.mode,
            scaffold_level=working.scaffold_level,
            message=message,
            question=question,
            context_label=working.context_label,
            context_reset=reset,
            objective_node_id=working.objective_node_id,
            concept_id=working.concept_id,
            awaiting_permission=working.awaiting_permission,
            out_of_scope=out_of_scope,
            revealed_answer=revealed,
        )

    def signal_context_reset(
        self, session_id: str, new_context: ContextLabel
    ) -> TutorTurn:
        working = self._state[session_id]
        previous = working.context_label
        working.context_label = new_context
        return TutorTurn(
            session_id=session_id,
            learner_id=working.learner_id,
            mode=working.mode,
            scaffold_level=working.scaffold_level,
            message=(
                f"Context reset: leaving {previous.value}, entering {new_context.value}. "
                "The scenario changed; do not reuse the previous record/transaction assumptions."
            ),
            question=self._question(working),
            context_label=new_context,
            context_reset=True,
            objective_node_id=working.objective_node_id,
            concept_id=working.concept_id,
            awaiting_permission=False,
            out_of_scope=False,
            revealed_answer=False,
        )
