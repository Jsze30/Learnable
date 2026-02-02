from dotenv import load_dotenv
import aiohttp

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool, RunContext
from livekit.plugins import noise_cancellation, silero, deepgram
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from parse_pdf import get_lecture_context

load_dotenv(".env")


@function_tool()
async def generate_visual_explanation(
    context: RunContext,
    user_prompt: str,
    source_pdf: str = "../backend/source_example/02-backtracking.pdf",
    model: str = "azure/gpt-5",
    max_videos: int = 1,
) -> str:
    """Generate visual explanations by calling the backend API.
    Only use this tool when the user specifically requests visual explanations.
    
    Args:
        user_prompt: The question or topic to explain visually
        source_pdf: Path to the PDF file to use as source material
        model: The model to use for generation
        max_videos: Maximum number of videos to generate
    """
    try:
        async with aiohttp.ClientSession() as session:
            with open(source_pdf, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('user_prompt', user_prompt)
                data.add_field('source_pdf', f, filename='source.pdf')
                data.add_field('model', model)
                data.add_field('max_videos', str(max_videos))
                
                async with session.post('http://localhost:3000/generate', data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return f"Visual explanation generated successfully"
                    else:
                        return f"Backend returned status {resp.status}"
    except Exception as e:
        return f"Error calling backend: {str(e)}"


class Assistant(Agent):
    def __init__(self, context: str = "") -> None:
        instructions = (
            "You are a helpful AI personal tutor. Answer questions about the provided course materials. "
            "Explain concepts clearly, provide examples when helpful, and keep responses concise and friendly. "
            "You are a voice assistant so only output text that is meant to be spoken aloud."
        )
        if context:
            instructions += f"\n\nCourse Materials:\n{context}"
        
        super().__init__(instructions=instructions, tools=[generate_visual_explanation])


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
        instructions="Greet the user and ask: how can I help you study today?"
    )
    print("[Agent] Initial greeting sent.")


if __name__ == "__main__":
    agents.cli.run_app(server)
