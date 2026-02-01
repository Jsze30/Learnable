from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero, deepgram
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from parse_pdf import get_lecture_context

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self, context: str = "") -> None:
        instructions = (
            "You are a helpful AI personal tutor. Answer questions about the provided course materials. "
            "Explain concepts clearly, provide examples when helpful, and keep responses concise and friendly. "
            "You are a voice assistant so only output text that is meant to be spoken aloud."
        )
        if context:
            instructions += f"\n\nCourse Materials:\n{context}"
        
        super().__init__(instructions=instructions)


server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    print("[Agent] Job received, waiting for room connection...")
    
    # Load lecture context
    lecture_context = get_lecture_context()
    context_content = lecture_context["content"]
    
    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4.1-mini",
        tts=deepgram.TTS(
            model="aura-2-neptune-en",
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(context=context_content),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=(
                    lambda params: noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )
    print(f"[Agent] Session started in room: {ctx.room.name}")

    await session.generate_reply(
        instructions="Greet the user and ask how you can assist them with the course materials."
    )
    print("[Agent] Initial greeting sent.")


if __name__ == "__main__":
    agents.cli.run_app(server)
