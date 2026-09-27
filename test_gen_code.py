import sys
sys.stdout.reconfigure(encoding='utf-8')
from ai_research_agents import IdeaGeneratorAgent, load_archetypes

idea_agent = IdeaGeneratorAgent(
    provider='omniroute',
    api_key='any',
    model='mistral/codestral-latest',
    endpoint='http://localhost:20128/v1'
)

archs = load_archetypes()
print(f"Total Archetypes: {len(archs)}")
for idx in [0, 4, 7]:
    arch = archs[idx]
    print(f"\n=================== ARCHETYPE {idx}: {arch['name']} ===================")
    prop = idea_agent.propose_strategy(idx)
    code = prop.get('code', '')
    print(code)
    break
