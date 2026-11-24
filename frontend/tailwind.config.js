/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1c1915",
        paper: "#f4efe6",
        card: "#fbf7f0",
        moss: "#1f6f5b",
        clay: "#b8612a",
        line: "#e3d9cb",
      },
      boxShadow: {
        panel: "0 20px 50px rgba(28, 25, 21, 0.12)",
      },
    },
  },
  plugins: [],
};
