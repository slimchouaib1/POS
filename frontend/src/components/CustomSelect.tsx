import React, { useState, useRef, useEffect, useMemo } from 'react';
import { ChevronDown, Check, Search } from 'lucide-react';

interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  style?: React.CSSProperties;
  className?: string;
}

export default function CustomSelect({ options, value, onChange, placeholder = "Select...", style, className = "" }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(o => o.value === value);

  const filteredOptions = useMemo(() => {
    if (!search.trim()) return options;
    const q = search.toLowerCase();
    return options.filter(o => o.label.toLowerCase().includes(q));
  }, [options, search]);

  // Reset highlight when filtered results change
  useEffect(() => {
    setHighlightedIndex(-1);
  }, [filteredOptions.length, search]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 0);
    } else {
      setSearch('');
      setHighlightedIndex(-1);
    }
  }, [isOpen]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[data-option]');
      if (items[highlightedIndex]) {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => Math.min(prev + 1, filteredOptions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < filteredOptions.length) {
          onChange(filteredOptions[highlightedIndex].value);
          setIsOpen(false);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        break;
    }
  };

  return (
    <div
      ref={containerRef}
      className={`custom-select-container ${className}`}
      style={{ position: 'relative', ...style }}
      onKeyDown={handleKeyDown}
    >
      {/* Trigger button */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none',
          backgroundColor: 'var(--color-bg-card)',
          color: selectedOption ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
          border: isOpen ? '1.5px solid var(--color-primary)' : '1.5px solid var(--color-border)',
          boxShadow: isOpen
            ? '0 0 0 3px rgba(220,38,38,0.12)'
            : '0 1px 2px rgba(0,0,0,0.04)',
          padding: '0.625rem 0.75rem',
          borderRadius: '10px',
          width: '100%',
          height: '100%',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          fontSize: '0.875rem',
        }}
        onClick={() => setIsOpen(!isOpen)}
        tabIndex={0}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown
          size={16}
          style={{
            color: 'var(--color-text-secondary)',
            transition: 'transform 0.25s ease',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            minWidth: 16,
          }}
        />
      </div>

      {/* Dropdown panel */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            backgroundColor: 'var(--color-bg-card)',
            border: '1.5px solid var(--color-border)',
            borderRadius: '12px',
            boxShadow:
              '0 20px 40px -8px rgba(0,0,0,0.15), 0 8px 16px -4px rgba(0,0,0,0.08)',
            zIndex: 100,
            overflow: 'hidden',
            animation: 'selectDropIn 0.18s ease-out',
          }}
        >
          {/* Search bar */}
          <div
            style={{
              padding: '8px 10px',
              borderBottom: '1px solid var(--color-border)',
              position: 'sticky',
              top: 0,
              backgroundColor: 'var(--color-bg-card)',
              zIndex: 2,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: 'var(--color-bg-page)',
                borderRadius: '8px',
                padding: '6px 10px',
                border: '1px solid var(--color-border)',
              }}
            >
              <Search size={14} style={{ color: 'var(--color-text-muted)', minWidth: 14 }} />
              <input
                ref={searchInputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Rechercher..."
                style={{
                  border: 'none',
                  outline: 'none',
                  background: 'transparent',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8125rem',
                  width: '100%',
                  fontFamily: 'inherit',
                }}
              />
            </div>
          </div>

          {/* Options list */}
          <div
            ref={listRef}
            role="listbox"
            style={{
              maxHeight: '220px',
              overflowY: 'auto',
              padding: '4px',
              scrollbarWidth: 'thin',
            }}
          >
            {filteredOptions.length === 0 ? (
              <div
                style={{
                  padding: '16px 12px',
                  color: 'var(--color-text-muted)',
                  fontSize: '0.8125rem',
                  textAlign: 'center',
                }}
              >
                Aucun résultat pour « {search} »
              </div>
            ) : (
              filteredOptions.map((option, index) => {
                const isSelected = value === option.value;
                const isHighlighted = index === highlightedIndex;
                return (
                  <div
                    key={option.value + index}
                    data-option
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => {
                      onChange(option.value);
                      setIsOpen(false);
                    }}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    style={{
                      padding: '8px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      borderRadius: '6px',
                      fontSize: '0.8125rem',
                      backgroundColor: isSelected
                        ? 'rgba(220,38,38,0.08)'
                        : isHighlighted
                        ? 'var(--color-bg-page)'
                        : 'transparent',
                      color: isSelected ? 'var(--color-primary)' : 'var(--color-text-primary)',
                      fontWeight: isSelected ? 600 : 400,
                      transition: 'background-color 0.1s',
                      gap: '8px',
                    }}
                  >
                    <span
                      style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        flex: 1,
                      }}
                    >
                      {option.label}
                    </span>
                    {isSelected && (
                      <Check
                        size={14}
                        style={{ color: 'var(--color-primary)', minWidth: 14 }}
                      />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Inline animation keyframes */}
      <style>{`
        @keyframes selectDropIn {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
