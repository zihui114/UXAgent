// src/composables/useForm.ts
import { reactive, watch } from 'vue'
import type { WizardForm } from '../types'

export function getWizardDefaults(): WizardForm {
  return {
    persona: {
      numSubjects: 20,
      generalIntent: 'Buy a jacket',
      examplePersona: `Persona: Clara
Background:
Clara is a PhD student in Computer Science at a prestigious university. She is deeply engaged in research focusing on artificial intelligence and machine learning, aiming to contribute to advancements in technology that can benefit society.

Demographics:

Age: 28
Gender: Female
Education: Pursuing a PhD in Computer Science
Profession: PhD student
Income: $50,000

Financial Situation:
Clara lives on her stipend as a PhD student and is careful with her spending. She prefers to save money for research-related expenses and invest in her academic pursuits.

Shopping Habits:
Clara dislikes shopping and avoids spending much time browsing through products. She prefers straightforward, efficient shopping experiences and often shops online for convenience. When she does shop, she looks for practicality and affordability over style or trendiness.
So Clara wants to shop QUICKLY and EFFICIENTLY.

Professional Life:
Clara spends most of her time in academia, attending conferences, working in the lab, and writing papers. Her commitment to her research is her main priority, and she manages her time around her academic responsibilities.

Personal Style:
Clara prefers comfortable, functional clothing, often choosing items that are easy to wear for long hours spent at her desk or in the lab. She wears medium-sized clothing and likes colors that reflect her personality—mostly red, which she finds uplifting and energizing.`,
      demographics: [
        {
          name: 'Age',
          choices: [
            { name: '18-55', weight: 1 },
          ]
        },
        {
          name: 'Gender',
          choices: [
            { name: 'Male', weight: 1 },
            { name: 'Female', weight: 1 },
            { name: 'Non-binary', weight: 1 },
          ]
        },
        {
          name: "Online Shopping Frequency",
          choices: [
            { name: 'A few times per year', weight: 1 },
            { name: 'option 2', weight: 1 },
            { name: 'option 3', weight: 1 },
          ]
        },
      ]
    },
    experiment: {
      startUrl: '',
      headless: true,
      maxSteps: 50,
      concurrency: 1, 
    },
    survey: {
      questionnaire: ''
    }
  }
}

export function createWizardForm() {
  const STORAGE_KEY = 'wizard_form'

  const defaults = getWizardDefaults()

  let saved: any = null
  try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null') } catch { saved = null }

  const form = reactive<WizardForm>({ ...defaults })
  if (saved && typeof saved === 'object') {
    try {
      if (saved.persona && typeof saved.persona === 'object') Object.assign(form.persona!, saved.persona)
      if (saved.experiment && typeof saved.experiment === 'object') Object.assign(form.experiment, saved.experiment)
      if (saved.survey && typeof saved.survey === 'object') Object.assign(form.survey, saved.survey)
    } catch {}
  }

  watch(form, (val) => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(val)) } catch {}
  }, { deep: true })

  return form
}


export type RunPayload = {
  total_personas: number
  demographics: { name: string; choices: { name: string; weight: number }[] }[]
  general_intent: string
  example_persona?: string
  start_url: string
  max_steps: number
  concurrency: number
  questionnaire: Record<string, any>
  headless: boolean
}

export function buildRunPayload(form: WizardForm): RunPayload {
  // parse questionnaire string to object
  let questionnaireObj: any = {}
  try { questionnaireObj = JSON.parse(form?.survey?.questionnaire ?? '{}') } catch { questionnaireObj = {} }

  return {
    total_personas: Number(form?.persona?.numSubjects ?? 0),
    demographics:   (form?.persona?.demographics ?? []).map(f => ({
      name: String(f?.name ?? '').trim(),
      choices: Array.isArray(f?.choices) ? f.choices.map(c => ({
        name: String(c?.name ?? '').trim(),
        weight: Number(c?.weight ?? 0) / 100
      })) : []
    })),
    general_intent: String(form?.persona?.generalIntent ?? ''),
    // Conditionally include only when enabled and non-empty
    ...(form?.persona?.useExamplePersona ? { example_persona: form?.persona?.examplePersona } :
        {example_persona: ''}),
    start_url:      String(form?.experiment?.startUrl ?? ''),
    max_steps:      Number(form?.experiment?.maxSteps ?? 0),
    concurrency:    Number(form?.experiment?.concurrency ?? 1),
    questionnaire:  questionnaireObj,
    headless:       Boolean(form?.experiment?.headless ?? true),
  }
}

export async function submitWizardForm(form: WizardForm) {
  const payload = buildRunPayload(form)
  const res = await fetch('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    // surface server’s error body to help you debug (400 shows missing fields)
    const text = await res.text()
    throw new Error(`Submit failed: ${res.status} ${text}`)
  }
  return await res.json()
}
