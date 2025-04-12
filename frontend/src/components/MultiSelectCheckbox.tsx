import { Checkbox } from "@/components/ui/checkbox";

interface MultiSelectCheckboxProps {
  label: string;
  options: { value: string; label: string }[];
  selectedValues: string[];
  onValueChange: (values: string[]) => void;
}

const MultiSelectCheckbox = ({
  label,
  options,
  selectedValues,
  onValueChange,
}: MultiSelectCheckboxProps) => {
  const handleCheckboxChange = (value: string, checked: boolean) => {
    if (checked) {
      onValueChange([...selectedValues, value]);
    } else {
      onValueChange(selectedValues.filter(v => v !== value));
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">{label}</h3>
      <div className="space-y-3">
        {options.map((option) => (
          <div key={option.value} className="flex items-center space-x-2">
            <Checkbox
              id={`${option.value}-checkbox`}
              checked={selectedValues.includes(option.value)}
              onCheckedChange={(checked) => 
                handleCheckboxChange(option.value, checked as boolean)
              }
            />
            <label
              htmlFor={`${option.value}-checkbox`}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {option.label}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};


export default MultiSelectCheckbox;