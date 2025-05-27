"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Search, CheckIcon } from "lucide-react";
import { cn } from "@/lib/utils";

// Ensure the array is always defined and initialized
const exampleTransactionIds = [
  "TX-12345",
  "TX-67890",
  "TX-11223",
  "TX-33445",
  "TX-55667",
  "TX-78901",
  "TX-23456",
  "TX-34567",
];

interface TransactionSearchProps {
  onSearch: (transactionId: string) => void;
}

export function TransactionSearch({ onSearch }: TransactionSearchProps) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [searchResults, setSearchResults] = useState<string[]>(exampleTransactionIds);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSearch(value);
    }
  };

  const handleSearch = (search: string) => {
    const filtered = exampleTransactionIds.filter(id => 
      id.toLowerCase().includes(search.toLowerCase())
    );
    setSearchResults(filtered);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full flex flex-col sm:flex-row gap-3">
      <div className="flex-1 flex-grow relative">
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <div className="w-full relative">
              <Input
                placeholder="Enter transaction ID..."
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-full pl-10"
              />
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
          </PopoverTrigger>
          <PopoverContent className="p-0" align="start">
            <Command shouldFilter={false}>
              <CommandInput 
                placeholder="Search transaction ID..." 
                onValueChange={handleSearch}
              />
              <CommandEmpty>No transaction found.</CommandEmpty>
              <CommandGroup>
                {searchResults.map((id) => (
                  <CommandItem
                    key={id}
                    value={id}
                    onSelect={(currentValue) => {
                      setValue(currentValue);
                      setOpen(false);
                    }}
                  >
                    {id}
                    <CheckIcon
                      className={cn(
                        "ml-auto h-4 w-4",
                        value === id ? "opacity-100" : "opacity-0"
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
            </Command>
          </PopoverContent>
        </Popover>
      </div>
      <Button type="submit" className="whitespace-nowrap">
        Analyze Transaction
      </Button>
    </form>
  );
}