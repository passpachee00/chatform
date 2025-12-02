import MockForm from "@/components/MockForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-lg rounded-lg p-8">
          <MockForm />
        </div>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            This is a mock form for testing the validation system.
          </p>
        </div>
      </div>
    </div>
  );
}
