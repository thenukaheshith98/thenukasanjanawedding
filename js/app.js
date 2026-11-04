const WEDDING = {
  start: new Date("2026-12-03T16:30:00+05:30"),
  end: new Date("2026-12-03T22:45:00+05:30"),
  title: "Wedding of Sanjana & Thenuka",
  location: "Paradise in Bolgoda, Crystal Ballroom, 67 Meegahawatte Rd, Piliyandala 10300, Sri Lanka",
  details:
    "Poruwa Ceremony — 04.30 PM\nRegistration — 05.15 PM\nReception — 06.00 PM\nEnd of Reception — 10.45 PM\nParadise in Bolgoda, Crystal Ballroom",
  rsvpEmail: "thenukaheshith@gmail.com",
  // Optional: Apps Script web app URL if you later connect Google Sheets directly
  rsvpSheetUrl: "",
};

const pad = (n) => String(n).padStart(2, "0");

function remaining(from, to) {
  const diff = Math.max(0, to.getTime() - from.getTime());
  const s = Math.floor(diff / 1000);
  return {
    days: Math.floor(s / 86400),
    hours: Math.floor((s % 86400) / 3600),
    minutes: Math.floor((s % 3600) / 60),
    seconds: s % 60,
    done: diff === 0,
  };
}

function tickCountdown() {
  const parts = remaining(new Date(), WEDDING.start);
  const map = {
    days: parts.days,
    hours: parts.hours,
    minutes: parts.minutes,
    seconds: parts.seconds,
  };
  Object.entries(map).forEach(([key, value]) => {
    document.querySelectorAll(`[data-count="${key}"]`).forEach((el) => {
      el.textContent = pad(value);
    });
  });
}

function icsStamp(date) {
  const y = date.getUTCFullYear();
  const m = pad(date.getUTCMonth() + 1);
  const d = pad(date.getUTCDate());
  const h = pad(date.getUTCHours());
  const min = pad(date.getUTCMinutes());
  const s = pad(date.getUTCSeconds());
  return `${y}${m}${d}T${h}${min}${s}Z`;
}

function buildIcs() {
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Sanjana and Thenuka//Wedding//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:sanjana-thenuka-wedding-${icsStamp(WEDDING.start)}@invitation`,
    `DTSTAMP:${icsStamp(new Date())}`,
    `DTSTART:${icsStamp(WEDDING.start)}`,
    `DTEND:${icsStamp(WEDDING.end)}`,
    `SUMMARY:${WEDDING.title}`,
    `LOCATION:${WEDDING.location}`,
    `DESCRIPTION:${WEDDING.details.replace(/\n/g, "\\n")}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
  return ics;
}

function downloadIcs() {
  const blob = new Blob([buildIcs()], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sanjana-thenuka-wedding.ics";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function googleCalUrl() {
  const dates = `${icsStamp(WEDDING.start)}/${icsStamp(WEDDING.end)}`;
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: WEDDING.title,
    dates,
    details: WEDDING.details,
    location: WEDDING.location,
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

function outlookUrl() {
  const params = new URLSearchParams({
    path: "/calendar/action/compose",
    rru: "addevent",
    subject: WEDDING.title,
    startdt: WEDDING.start.toISOString(),
    enddt: WEDDING.end.toISOString(),
    body: WEDDING.details,
    location: WEDDING.location,
  });
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
}

function setupCalendar() {
  const root = document.querySelector("[data-calendar]");
  if (!root) return;
  const toggle = root.querySelector("[data-calendar-toggle]");
  const google = root.querySelector("[data-cal-google]");
  const outlook = root.querySelector("[data-cal-outlook]");
  const apple = root.querySelector("[data-cal-apple]");
  const ics = root.querySelector("[data-cal-ics]");

  if (google) google.href = googleCalUrl();
  if (outlook) outlook.href = outlookUrl();

  const close = () => {
    root.classList.remove("is-open");
    toggle?.setAttribute("aria-expanded", "false");
  };

  toggle?.addEventListener("click", () => {
    const open = !root.classList.contains("is-open");
    root.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  });

  apple?.addEventListener("click", downloadIcs);
  ics?.addEventListener("click", downloadIcs);

  document.addEventListener("click", (e) => {
    if (!root.contains(e.target)) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

function setupMusic() {
  const audio = document.querySelector("[data-audio]");
  const buttons = document.querySelectorAll("[data-music]");
  if (!audio) return;

  const setState = (playing) => {
    buttons.forEach((btn) => {
      btn.classList.toggle("is-playing", playing);
      btn.setAttribute("aria-label", playing ? "Turn music off" : "Turn music on");
      btn.setAttribute("title", playing ? "Turn music off" : "Turn music on");
    });
  };

  const play = async () => {
    try {
      audio.volume = 0.55;
      await audio.play();
      setState(true);
    } catch {
      setState(false);
    }
  };

  const pause = () => {
    audio.pause();
    setState(false);
  };

  buttons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (audio.paused) play();
      else pause();
    });
  });

  audio.addEventListener("ended", () => setState(false));
  return { play, pause, audio };
}

function setupCover(music) {
  const cover = document.querySelector("[data-cover]");
  const openBtn = document.querySelector("[data-open]");
  if (!cover || !openBtn) return;

  const open = () => {
    document.body.classList.remove("is-locked");
    document.body.classList.add("is-open");
    cover.classList.add("is-gone");
    cover.setAttribute("aria-hidden", "true");
    music?.play();
    window.setTimeout(() => {
      cover.hidden = true;
    }, 700);
  };

  openBtn.addEventListener("click", open);
}

function cleanText(value, max) {
  return String(value || "")
    .replace(/[\u0000-\u001F\u007F]/g, "")
    .trim()
    .slice(0, max);
}

function rsvpBody(data) {
  return [
    "RSVP for Sanjana & Thenuka",
    "Please respond by 15 November 2026",
    "",
    `Name: ${data.name}`,
    `Mobile: ${data.mobile || "—"}`,
    `Will you attend?: ${data.attend}`,
    `Number in your party: ${data.party}`,
    `Events: ${data.events || "—"}`,
    `Meal preference: ${data.meal || "—"}`,
    `Note: ${data.note || "—"}`,
  ].join("\n");
}

function sendRsvpToSheet(url, payload) {
  const body = new URLSearchParams({
    name: payload.name,
    mobile: payload.mobile,
    attend: payload.attend,
    party: payload.party,
    events: payload.events,
    meal: payload.meal,
    note: payload.note,
  });
  return fetch(url, { method: "POST", body }).catch(() =>
    fetch(url, { method: "POST", mode: "no-cors", body })
  );
}

function mailtoRsvp(email, payload) {
  const subject = `RSVP — ${payload.name} — Sanjana & Thenuka`;
  const to = email ? `mailto:${encodeURIComponent(email)}` : "mailto:";
  return `${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(rsvpBody(payload))}`;
}

function sendRsvpToInbox(email, payload) {
  const body = new FormData();
  body.append("Name", payload.name);
  body.append("Mobile", payload.mobile || "—");
  body.append("Attend", payload.attend);
  body.append("Party", payload.party);
  body.append("Events", payload.events || "—");
  body.append("Meal", payload.meal || "—");
  body.append("Note", payload.note || "—");
  body.append("_subject", `RSVP — ${payload.name} — Sanjana & Thenuka`);
  body.append("_template", "table");
  body.append("_captcha", "false");

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 4000);
  return fetch(`https://formsubmit.co/ajax/${encodeURIComponent(email)}`, {
    method: "POST",
    headers: { Accept: "application/json" },
    body,
    signal: controller.signal,
  })
    .finally(() => window.clearTimeout(timer))
    .then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.success === false || data.success === "false") {
        throw new Error(data.message || "RSVP save failed");
      }
    });
}

function setupRsvp() {
  const form = document.querySelector("[data-rsvp-form]");
  if (!form) return;

  const errorEl = form.querySelector("[data-rsvp-error]");
  const successEl = form.querySelector("[data-rsvp-success]");
  const submitBtn = form.querySelector("[data-rsvp-submit]");
  const submitLabel = form.querySelector("[data-rsvp-submit-label]");
  const partyInput = form.querySelector('input[name="party"]');
  const eventInputs = [...form.querySelectorAll('input[name="events"]')];

  const showError = (message) => {
    if (!errorEl) return;
    errorEl.hidden = !message;
    errorEl.textContent = message || "";
  };

  const setAttendState = () => {
    const attend = form.querySelector('input[name="attend"]:checked')?.value;
    const declining = attend === "No";
    if (partyInput) {
      partyInput.disabled = declining;
      if (declining) partyInput.value = "0";
      else if (partyInput.value === "0") partyInput.value = "1";
    }
    eventInputs.forEach((input) => {
      input.disabled = declining;
      if (declining) input.checked = false;
    });
  };

  form.querySelectorAll('input[name="attend"]').forEach((input) => {
    input.addEventListener("change", setAttendState);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    showError("");
    if (successEl) successEl.hidden = true;

    const name = cleanText(form.name.value, 80);
    const mobile = cleanText(form.mobile.value, 20);
    const attend = form.querySelector('input[name="attend"]:checked')?.value || "";
    const party = attend === "No" ? "0" : String(form.party.value || "").trim();
    const events = eventInputs.filter((input) => input.checked).map((input) => input.value);
    const meal = cleanText(form.meal.value, 80);
    const note = cleanText(form.note.value, 500);

    if (!name) {
      showError("Please enter your name.");
      form.name.focus();
      return;
    }
    if (!attend) {
      showError("Please tell us if you will attend.");
      return;
    }
    if (attend !== "No") {
      const partyCount = Number(party);
      if (!Number.isInteger(partyCount) || partyCount < 1 || partyCount > 20) {
        showError("Please enter a party size between 1 and 20.");
        partyInput?.focus();
        return;
      }
    }

    const payload = {
      name,
      mobile,
      attend,
      party,
      events: events.join(", "),
      meal,
      note,
    };

    const sheetUrl = String(WEDDING.rsvpSheetUrl || "").trim();
    const recipient = String(WEDDING.rsvpEmail || "").trim();

    if (submitBtn) submitBtn.disabled = true;

    const finish = (ok, message, resetForm) => {
      if (submitBtn) submitBtn.disabled = false;
      if (submitLabel) submitLabel.textContent = "Send RSVP";
      if (ok) {
        if (resetForm) {
          form.reset();
          setAttendState();
        }
        if (successEl) {
          successEl.hidden = false;
          successEl.textContent = message;
        }
        return;
      }
      showError(message);
    };

    const honey = cleanText(form.querySelector('[name="_gotcha"]')?.value, 80);
    if (honey) {
      finish(true, "Thank you — your RSVP has been saved.", true);
      return;
    }

    if (sheetUrl) {
      if (submitLabel) submitLabel.textContent = "Sending…";
      sendRsvpToSheet(sheetUrl, payload)
        .then(() => finish(true, "Thank you — your RSVP has been saved.", true))
        .catch(() => finish(false, "Could not save your RSVP. Please try again."));
      return;
    }

    if (recipient) {
      if (submitLabel) submitLabel.textContent = "Sending…";
      sendRsvpToInbox(recipient, payload)
        .then(() => finish(true, "Thank you — your RSVP has been saved.", true))
        .catch(() => {
          window.location.href = mailtoRsvp(recipient, payload);
          finish(true, "Thank you — your email app will send this RSVP.", false);
        });
      return;
    }

    if (submitLabel) submitLabel.textContent = "Opening…";
    window.location.href = mailtoRsvp("", payload);
    finish(true, "Thank you — your email app will send this RSVP.", false);
  });
}

function setupNav() {
  const links = document.querySelectorAll(".dock a[href^='#']");
  const sections = [...links]
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  const setActive = (id) => {
    links.forEach((link) => {
      link.classList.toggle("is-active", link.getAttribute("href") === `#${id}`);
    });
  };

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target?.id) setActive(visible.target.id);
    },
    { rootMargin: "-35% 0px -50% 0px", threshold: [0.2, 0.4, 0.6] }
  );

  sections.forEach((section) => observer.observe(section));
}

document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("is-locked");
  tickCountdown();
  window.setInterval(tickCountdown, 1000);
  setupCalendar();
  setupRsvp();
  const music = setupMusic();
  setupCover(music);
  setupNav();
});
