Suggested order of reading:

**1) Writeup.md:** gives you an overview of what i've done

**2) The actual tool itself**
- **.claude/skills:** the skills that are invoked through the pipeline, representing the kick-off (`merger-run.md`), five stages (intake->source-plan->research->expert->red-team), and the eval (`eval.md`)
- **.clalude/agents:** the agent workers that are used in the five stages
- **tool/config & /methodology:** deal-agnostic methodology that a domain expert would tweak and reflects the business acumen component of the task
- **tool/runs:** two actual runs: cintas_unifirst (me + the tool worked together) and paramoutn_wbd (the tool worked by itself). Eval folder sits here
  
**3) tool/README.md:** Try the tool out yourself. You'll need Claude Code and a reasonably high usage limit (I used the MAX plan)
