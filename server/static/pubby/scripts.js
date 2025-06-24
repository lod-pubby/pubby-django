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
