const fs = require('fs');
const path = 'web/src/components/analisis/PanelAnalisis.astro';
let content = fs.readFileSync(path, 'utf8');

// Update cerrarMenus
content = content.replace(
  `  function cerrarMenus(): void {
    document
      .querySelectorAll<HTMLElement>('[data-menu-panel]')
      .forEach((menu) => {
        menu.hidden = true;
      });
    document
      .querySelectorAll<HTMLButtonElement>('[data-boton-menu-panel]')
      .forEach((boton) => {
        boton.setAttribute('aria-expanded', 'false');
      });
  }`,
  `  function cerrarMenus(devolverFoco = false): void {
    const menusAbiertos = document.querySelectorAll<HTMLElement>('[data-menu-panel]:not([hidden])');
    let panelIdParaFoco: string | null = null;
    if (devolverFoco && menusAbiertos.length > 0) {
        panelIdParaFoco = menusAbiertos[0].dataset.menuPanel || null;
    }

    document
      .querySelectorAll<HTMLElement>('[data-menu-panel]')
      .forEach((menu) => {
        menu.hidden = true;
      });
    document
      .querySelectorAll<HTMLButtonElement>('[data-boton-menu-panel]')
      .forEach((boton) => {
        boton.setAttribute('aria-expanded', 'false');
        if (devolverFoco && panelIdParaFoco && boton.dataset.botonMenuPanel === panelIdParaFoco) {
            boton.focus();
        }
      });
  }`
);

// Update Escape listener
content = content.replace(
  `  document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape') cerrarMenus();
  });`,
  `  document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape') cerrarMenus(true);
  });`
);

// Update menu click listener
content = content.replace(
  `      if (accion === 'ocultar') {
        actualizarLayoutAnalisis({
          panelesVisibles: obtenerLayoutAnalisis().panelesVisibles.filter(
            (panelId) => panelId !== id,
          ),
        });
      }
      cerrarMenus();
    });`,
  `      if (accion === 'ocultar') {
        actualizarLayoutAnalisis({
          panelesVisibles: obtenerLayoutAnalisis().panelesVisibles.filter(
            (panelId) => panelId !== id,
          ),
        });
      }
      cerrarMenus(true);
    });`
);

fs.writeFileSync(path, content, 'utf8');
