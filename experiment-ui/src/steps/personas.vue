<template>
  <n-card>
    <n-form ref="formRef" :model="form">
      <!-- ===================== META (count + intent) ===================== -->
      <n-divider style="margin-top: 0">Recruitment Target Setting</n-divider>
      <div class="meta">
        <div class="form-row">
          <n-form-item
            label="URL of website being tested"
            :path="`experiment.startUrl`"
            :rule="{
              required: true,
              message: 'Please enter a URL',
            }"
          >
            <n-input
              v-model:value="form.experiment.startUrl"
              placeholder="https://www.example.com"
              class="wide"
            />
          </n-form-item>
        </div>

        <div class="form-row">
          <n-form-item
            label="Number of Participants"
            :path="`persona.numSubjects`"
            :rule="{
              required: true,
              message: 'Please input the number of participants',
            }"
          >
            <n-input-number
              v-model:value="form.persona!.numSubjects"
              :min="1"
              :step="1"
              class="narrow"
              placeholder="e.g., 15"
            />
          </n-form-item>
        </div>

        <div class="form-row">
          <n-form-item
            label="Participant Task"
            :path="`persona.generalIntent`"
            :rule="{
              required: true,
              message: 'Please input the participant task',
            }"
          >
            <n-input
              v-model:value="form.persona!.generalIntent"
              class="wide"
              placeholder="e.g., Purchase an indoor volleyball"
            />
          </n-form-item>
        </div>

        <div class="field full">
          <n-form-item
            label="Example Persona"
            :path="`persona.examplePersona`"
            :rule="{
              required: true,
              message: 'Please input the example persona',
            }"
          >
            <n-input
              type="textarea"
              v-model:value="form.persona!.examplePersona"
              class="wide"
              placeholder="Input an example persona that is used as format reference. Generated personas will follow the same format."
            />
          </n-form-item>
        </div>
      </div>

      <n-divider>Demographics</n-divider>

      <!-- Empty state -->
      <n-alert
        v-if="form.persona!.demographics.length === 0"
        type="info"
        class="mb-2"
      >
        No demographic fields yet.
      </n-alert>

      <!-- Fields list -->
      <div class="fields">
        <n-card
          v-for="(field, fi) in form.persona!.demographics"
          :key="fi"
          class="field-card"
        >
          <div class="field-header">
            <div class="field-name">
              <label class="form-label">Field Name</label>
              <n-input
                v-model:value="field.name"
                placeholder="e.g., Age, Gender, Income, Occupation, etc."
                @focus="(e: FocusEvent) => selectAll(e)"
              />
            </div>
          </div>

          <!-- Choices -->
          <div class="choices">
            <div class="choice header">
              <div class="col label">Value</div>
              <div class="col weight">Weight</div>
              <!--            <div class="col pct">%</div>-->
              <div class="col actions">Actions</div>
            </div>

            <div
              class="choice"
              v-for="(choice, ci) in field.choices"
              :key="`${fi}-${ci}`"
            >
              <div class="col label">
                <n-input
                  v-model:value="choice.name"
                  placeholder="e.g., 18-24, Male"
                  @focus="(e: FocusEvent) => selectAll(e)"
                />
              </div>
              <div class="col weight">
                <n-input-number v-model:value="choice.weight" :min="0" />
              </div>
              <div class="col actions">
                <n-popconfirm @positive-click="removeChoice(fi, ci)">
                  <template #trigger>
                    <n-button
                      tertiary
                      type="error"
                      :disabled="field.choices.length <= 1"
                      size="tiny"
                    >
                      <template #icon
                        ><n-icon><MdTrash /></n-icon
                      ></template>
                      Remove Value
                    </n-button>
                  </template>
                  Remove {{ choice.name || "this choice" }}?
                </n-popconfirm>
              </div>
            </div>
          </div>

          <div class="field-footer">
            <n-button secondary size="tiny" @click="addChoice(fi)">
              <template #icon
                ><n-icon><MdAdd /></n-icon
              ></template>
              Add Choice</n-button
            >

            <n-popconfirm @positive-click="removeField(fi)">
              <template #trigger>
                <n-button tertiary type="error" size="tiny">
                  <template #icon
                    ><n-icon><MdTrash /></n-icon
                  ></template>
                  Remove Field
                </n-button>
              </template>
              Remove {{ field.name || "this field" }}?
            </n-popconfirm>
          </div>
        </n-card>
      </div>

      <!-- Add field toolbar -->
      <div class="toolbar">
        <div class="left">
          <n-button @click="addField" secondary size="tiny">
            <template #icon
              ><n-icon><MdAdd /></n-icon
            ></template>
            Add Field</n-button
          >
        </div>
      </div></n-form
    >

    <!-- ===================== ACTIONS ===================== -->
    <template #action>
      <div class="card-nav">
        <n-button type="error" @click="handleReset" secondary
          >Reset Form</n-button
        >
        <div class="space"></div>
        <n-button type="primary" @click="handleNext">
          Next <n-icon><MdArrowRoundForward /></n-icon>
        </n-button>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { inject, computed, ref } from "vue";
import { FORM_KEY, NAV_KEY, type WizardForm, type WizardNav } from "../types";
import { MdArrowRoundForward, MdTrash, MdAdd } from "@vicons/ionicons4";
import { getWizardDefaults } from "../composables/useForm";
import type { FormInst } from "naive-ui";

const form = inject<WizardForm>(FORM_KEY)!;
const nav = inject<WizardNav>(NAV_KEY)!;
const formRef = ref<FormInst | null>(null);

// For number input, allow temporary null/empty while editing; apply on blur
const pendingByChoiceId = new Map<string, number | null>();

function urlValidator(_: any, value: string) {
  if (!value) return new Error("Please enter a URL");
  try {
    // Allow missing protocol by attempting to prepend https:// for check
    const hasProtocol = /^(https?:)\/\//i.test(value);
    // eslint-disable-next-line no-new
    new URL(hasProtocol ? value : `https://${value}`);
    return true;
  } catch {
    return new Error("Please enter a valid URL");
  }
}

function selectAll(e: FocusEvent) {
  const target = e.target as HTMLInputElement | null;
  if (target && typeof target.select === "function") {
    requestAnimationFrame(() => {
      try {
        target.select();
      } catch {}
    });
  }
}

/* ---------------------- Submit ---------------------- */
const isValidMeta = computed(() => {
  const hasValidUrl = (() => {
    const url = form.experiment.startUrl;
    if (!url) return false;
    try {
      const hasProtocol = /^(https?:)\/\//i.test(url);
      new URL(hasProtocol ? url : `https://${url}`);
      return true;
    } catch {
      return false;
    }
  })();

  return (
    hasValidUrl &&
    Number.isFinite(form.persona!.numSubjects) &&
    (form.persona!.numSubjects as number) >= 1 &&
    String(form.persona!.generalIntent || "").trim().length > 0
  );
});

function handleReset() {
  try {
    localStorage.removeItem("wizard_form");
  } catch {}
  const defaults = getWizardDefaults();
  // Reset persona
  form.persona!.numSubjects = defaults.persona.numSubjects;
  form.persona!.generalIntent = defaults.persona.generalIntent;
  form.persona!.examplePersona = defaults.persona.examplePersona;
  form.persona!.demographics = JSON.parse(
    JSON.stringify(defaults.persona.demographics)
  );
  // Reset experiment
  form.experiment.startUrl = defaults.experiment.startUrl;
  form.experiment.headless = defaults.experiment.headless;
  form.experiment.maxSteps = defaults.experiment.maxSteps;
  form.experiment.concurrency = defaults.experiment.concurrency;
  // Reset survey
  form.survey.questionnaire = defaults.survey.questionnaire;
  // Clear any pending inline edits
  pendingByChoiceId.clear();
}

function addChoice(fieldIndex: number) {
  form.persona!.demographics[fieldIndex].choices.push({
    name: "",
    weight: 0,
  });
}

function removeChoice(fieldIndex: number, choiceIndex: number) {
  const field = form.persona!.demographics[fieldIndex];
  if (!field) return;
  field.choices.splice(choiceIndex, 1);
  if (field.choices.length === 0) {
    field.choices.push({ name: "", weight: 1 });
    return;
  }
}

function addField() {
  form.persona!.demographics.push({
    name: "",
    choices: [{ name: "", weight: 1 }],
  });
}

function removeField(fieldIndex: number) {
  form.persona!.demographics.splice(fieldIndex, 1);
}

function handleNext() {
  formRef.value?.validate().then((valid) => {
    if (valid) {
      nav.next();
    }
  });
}
</script>

<style scoped lang="scss">
/* Top meta */
.meta {
  display: grid;
  gap: 8px;
  margin-bottom: 8px;

  .form-row {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;

    .n-input {
      width: 100%;
    }
    .n-form-item {
      width: 100%;
    }
  }
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 8px;

  .left,
  .right {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}

.fields {
  display: grid;
  gap: 10px;

  .field-card {
    .field-header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      .field-name {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      .n-input {
        flex: 1;
      }

      .field-actions {
        display: flex;
        align-items: center;
      }
    }

    .field-footer {
      margin-top: 6px;
      gap: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      justify-content: flex-end;
    }
  }
}

.choices {
  display: grid;
  gap: 8px;

  .choice {
    display: grid;
    grid-template-columns: 1.7fr 1.7fr 120px auto;
    gap: 8px;
    align-items: center;
    height: 34px;
  }

  .choice.header {
    font-weight: 600;
    background: transparent;
    box-shadow: none;
    padding: 0 8px;
    .actions {
      justify-content: center;
    }
  }

  .col.actions {
    display: flex;
    gap: 6px;
    justify-content: flex-end;
  }
}

.card-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.wide {
  max-width: 400px; /* Start URL */
}
</style>
