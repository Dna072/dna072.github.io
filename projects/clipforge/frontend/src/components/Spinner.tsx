export function Spinner() {
  return <div className="spinner" aria-label="Loading" />;
}

export function FullPageSpinner() {
  return (
    <div className="center-screen">
      <Spinner />
    </div>
  );
}
