(function () {
    'use strict';

    const storageKey = 'copilot-sdk-workshop.language';
    const picker = document.getElementById('languagePicker');
    const languageInputs = [...document.querySelectorAll('input[name="language"]')];
    const startLink = document.getElementById('startWorkshopLink');
    const docsLink = document.getElementById('sdkDocsLink');
    const summary = document.getElementById('languageSummary');
    const installCommand = document.getElementById('installCommand');
    const runtimeNote = document.getElementById('runtimeNote');
    const workshopInputs = [...document.querySelectorAll('input[name="workshop"]')];
    const targetAppLink = document.getElementById('targetAppLink');
    const previewTitle = document.getElementById('previewTitle');
    const preview = document.getElementById('workshopPreview');
    const startGuidance = document.getElementById('startGuidance');
    let selectedWorkshopId = null;

    const workshops = {
        sdlc: {
            name: 'Accessibility reviewer',
            previewTitle: 'accessibility-reviewer',
            preview: `URL → Playwright inspection
     → WCAG lookup
     → structured report

[tool] playwright-browser_navigate
[tool] accessibility_rule_lookup

Finding
The name input has no accessible name.`,
            guidance: 'Build an SDLC developer tool in a 90-minute core workshop.'
        },
        museum: {
            name: 'Museum Exhibit Studio',
            previewTitle: 'museum-exhibit-studio',
            preview: `Approved facts → curator session
               → exhibit validation
               → visitor-ready copy

Available tools: []
System message: replace

# Journey to the Moon
## Narrative
## Visitor questions`,
            guidance: 'Build a non-SDLC curator CLI in a 105-minute core workshop.'
        }
    };

    function getStoredLanguageId() {
        try {
            return window.localStorage.getItem(storageKey);
        } catch (error) {
            return null;
        }
    }

    function storeLanguageId(languageId) {
        try {
            window.localStorage.setItem(storageKey, languageId);
        } catch (error) {
            // Local storage can be unavailable in private browsing contexts.
        }
    }

    function updateSelection(languageId) {
        const language = WorkshopLanguages.getLanguage(languageId);
        const hasLanguage = language !== null;
        const workshop = selectedWorkshopId ? workshops[selectedWorkshopId] : null;
        const ready = workshop !== null && hasLanguage;

        picker.disabled = workshop === null;
        document.querySelectorAll('.language-option').forEach(option => {
            option.classList.toggle('selected', option.dataset.language === language?.id);
        });
        startLink.classList.toggle('disabled', !ready);
        startLink.setAttribute('aria-disabled', String(!ready));
        startLink.href = ready
            ? WorkshopLanguageNavigation.firstLessonUrl(language.id, selectedWorkshopId)
            : workshop ? '#language-picker' : '#workshop-picker';
        startLink.textContent = ready ? `Start ${workshop.name}` : 'Start selected workshop';
        targetAppLink.hidden = selectedWorkshopId !== 'sdlc';

        if (!hasLanguage) {
            docsLink.removeAttribute('href');
            docsLink.setAttribute('aria-disabled', 'true');
            summary.textContent = workshop
                ? `Now choose a language for ${workshop.name}.`
                : 'Choose a workshop first, then select its implementation language.';
            installCommand.textContent = '';
            runtimeNote.textContent = '';
            startGuidance.textContent = workshop?.guidance ??
                'Choose a workshop and language. No prior agent or SDK experience required.';
            return;
        }

        docsLink.href = language.docsUrl;
        docsLink.removeAttribute('aria-disabled');
        docsLink.textContent = `${language.displayName} SDK docs ↗`;
        summary.textContent = workshop
            ? `${workshop.name} will use the ${language.displayName} SDK.`
            : 'Choose a workshop to continue.';
        installCommand.textContent = language.installCommand;
        runtimeNote.textContent = language.runtimeNote;
        startGuidance.textContent = workshop?.guidance ?? 'Choose a workshop to continue.';
    }

    function selectWorkshop(workshopId) {
        selectedWorkshopId = workshops[workshopId] ? workshopId : null;
        document.querySelectorAll('.workshop-option').forEach(option => {
            option.classList.toggle('selected', option.dataset.workshop === selectedWorkshopId);
        });
        const workshop = selectedWorkshopId ? workshops[selectedWorkshopId] : null;
        previewTitle.textContent = workshop?.previewTitle ?? 'workshop-preview';
        preview.textContent = workshop?.preview ?? 'Select a workshop to preview its agent flow.';
        updateSelection(languageInputs.find(input => input.checked)?.value ?? null);
        if (workshop) {
            languageInputs[0].focus();
        }
    }

    languageInputs.forEach(input => {
        input.addEventListener('change', () => {
            const language = WorkshopLanguages.getLanguage(input.value);
            storeLanguageId(language.id);
            updateSelection(language.id);
        });
    });

    workshopInputs.forEach(input => {
        input.addEventListener('change', () => selectWorkshop(input.value));
    });

    startLink.addEventListener('click', event => {
        if (startLink.getAttribute('aria-disabled') === 'true') {
            event.preventDefault();
            if (!selectedWorkshopId) {
                workshopInputs[0].focus();
            } else {
                languageInputs[0].focus();
                languageInputs[0].reportValidity();
            }
        }
    });

    const initialLanguage = WorkshopLanguageNavigation.resolveLanguage(
        window.location.search,
        getStoredLanguageId(),
        WorkshopLanguages.getLanguage
    );
    if (initialLanguage) {
        const matchingLanguage = languageInputs.find(input => input.value === initialLanguage.id);
        matchingLanguage.checked = true;
        storeLanguageId(initialLanguage.id);
    }

    const requestedWorkshop = new URLSearchParams(window.location.search).get('workshop');
    const matchingWorkshop = workshopInputs.find(input => input.value === requestedWorkshop);
    if (matchingWorkshop) {
        matchingWorkshop.checked = true;
        selectWorkshop(matchingWorkshop.value);
    } else {
        updateSelection(initialLanguage?.id ?? null);
    }
}());
