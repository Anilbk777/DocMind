import styles from "./Modal.module.css";

export default function ConfirmationModal({ isOpen, title, message, onConfirm, onCancel, confirmText = "Delete", cancelText = "Cancel", isLoading = false }) {
  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>

          {!isLoading && (
            <button className={styles.closeBtn} onClick={onCancel}>
              &times;
            </button>
          )}
        </div>
        <div className={styles.body}>
          <p>{message}</p>
        </div>
        <div className={styles.footer}>

          {!isLoading && (
            <button className={styles.cancelBtn} onClick={onCancel}>
              {cancelText}
            </button>
          )}
          <button className={styles.confirmBtn} onClick={onConfirm} disabled={isLoading}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
