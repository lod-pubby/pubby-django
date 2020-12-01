//
//Script for dark mode
//

if (localStorage.getItem("dark-mode"))
  document.querySelector("html").classList.add("dark-mode")

document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("a.switch-mode").addEventListener("click", event => {
    const darkModeEnabled = document.querySelector("html").classList.toggle("dark-mode")
    if (darkModeEnabled)
      localStorage.setItem("dark-mode", true)
    else
      localStorage.removeItem("dark-mode")
    event.preventDefault()
  })
})


//
// Language switcher for predicate labels
//
document.addEventListener("DOMContentLoaded", () => {
  const langSpanContainers = new Set(Array.from(document.querySelectorAll("span[lang]")).map(span => span.parentElement))

  function switchToLanguage(targetLang) {
    for (container of langSpanContainers) {
      const spans = Array.from(container.querySelectorAll("span"))

      const tryToShowSpansWith = (targetLang) => {
        const matchingSpans = spans.filter(span => span.getAttribute("lang") === targetLang)
        if (matchingSpans.length > 0) {
          matchingSpans.forEach(span => span.style.display = "initial")
          spans.filter(span => span.getAttribute("lang") != targetLang).forEach(span => span.style.display = "none")
          return true
        } else {
          return false
        }
      }

      if (targetLang == "all") {
        spans.forEach(span => span.style.display = "initial")
        continue
      }

      // show spans with matching lang tag
      if (tryToShowSpansWith(targetLang))
        continue
      // if empty: show spans with lang "en"
      if (tryToShowSpansWith("en"))
        continue
      // if empty: show spans without lang attribute
      if (tryToShowSpansWith(null))
        continue

      // if empty: show all spans
      spans.forEach(span => span.style.display = "initial")
    }

    localStorage.setItem("language", targetLang)
  }

  // Create language switcher links
  const allLangs = new Set(Array.from(document.querySelectorAll("span[lang]")).map(span => span.getAttribute("lang")))
  for (let lang of Array.from(allLangs).sort()) {
    const a = document.createElement("a")
    a.setAttribute("href", "#")
    a.setAttribute("lang", lang)
    a.textContent = lang

    a.addEventListener("click", event => {
      switchToLanguage(lang)
      event.preventDefault()
    })

    document.querySelector("nav span.languages").append(a)
  }

  const a = document.createElement("a")
  a.setAttribute("href", "#")
  a.textContent = "all"

  a.addEventListener("click", event => {
    switchToLanguage("all")
    event.preventDefault()
  })

  document.querySelector("nav span.languages").append(a)

  // Switch to stored language
  if (localStorage.getItem("language"))
    switchToLanguage(localStorage.getItem("language"))
})
