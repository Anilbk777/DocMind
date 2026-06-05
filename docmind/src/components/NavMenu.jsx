import { NavLink } from "react-router-dom";
import styles from "./Sidebar.module.css";

export default function NavMenu() {
  return (
    <nav className={styles.navMenu}>
      <div className={styles.navGroup}>
        <NavLink 
          to="/app/chat" 
          className={({ isActive }) => 
            `${styles.navLink} ${isActive ? styles.navLinkActive : ""}`
          }
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          Chat
        </NavLink>
        
        <NavLink 
          to="/app/library" 
          className={({ isActive }) => 
            `${styles.navLink} ${isActive ? styles.navLinkActive : ""}`
          }
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Library
        </NavLink>
      </div>
    </nav>
  );
}
