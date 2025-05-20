/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    fontFamily: {
      sans: ["Poppins", "Sarabun", "sans-serif"],
    },
    extend: {
      screens: {
        sm: "640px",
        md: "768px",
        lg: "1024px",
      },
      colors: {
        primary: "#FEF7FF",
        secondary: "#FFC0CB",
        "button-primary": "#FF69B4",
        "button-primary-darker": "#FF1493",
        "button-primary-active": "#FF8DA1",
        "app-bg": "#fcf6ff",
        "card-bg": "#f5eaf9",
        "profile-bg": "#e8d5f5",
        "add-button": "#ffd6e6",
        "add-button-hover": "#ffc2d3",
      },
    },
  },
  plugins: [],
};
